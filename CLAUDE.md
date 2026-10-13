# agora — Claude Code Instructions

> **Core rule**: this file is **preferences, process, and procedures** — durable rules that change rarely. Volatile state (current version, binary sizes, test counts, in-flight work, consumers) lives in [`docs/development/state.md`](docs/development/state.md), refreshed every release. Do not inline state here — inlined state rots within a minor.

---

## Project Identity

**agora** (Greek **ἀγορά**: civic marketplace, public assembly) — telnet-served BBS for the AGNOS ecosystem. Posts, messages, file-share. Cyrius-native.

- **Type**: Binary (BBS server)
- **License**: GPL-3.0-only
- **Language**: Cyrius (toolchain pinned in `cyrius.cyml [package].cyrius`)
- **Version**: `VERSION` at the project root is the source of truth — do not inline the number here
- **Genesis repo**: [agnosticos](https://github.com/MacCracken/agnosticos)
- **Standards**: [First-Party Standards](https://github.com/MacCracken/agnosticos/blob/main/docs/development/planning/first-party-standards.md) · [First-Party Documentation](https://github.com/MacCracken/agnosticos/blob/main/docs/development/planning/first-party-documentation.md)
- **Naming lane**: Greek — agora opens this lane in the AGNOS ecosystem alongside the existing Sanskrit/Hindi (system libs) and English-wordplay/Polynesian (user-facing tools) lanes. Three convergent layers: ancient ἀγορά + Doja Cat "Agora Hills" (Scarlet, 2023) + Agoura Hills CA (adjacent to project home base).

## Goal

Own the **public-assembly surface** of an AGNOS deployment: a multi-user, telnet-served bulletin board where citizens of a LAN gather to post, read, share files, and argue. Cross-platform from M1 — Linux today via cyrius `lib/net.cyr`, AGNOS / macOS / Windows follow as the stdlib grows backends. Companion to the separate MUD userland (same telnet substrate, different application semantics).

## Current State

> Volatile state lives in [`docs/development/state.md`](docs/development/state.md) — current version, binary size, in-flight slot, recent releases, consumer status, gate state for downstream milestones. Refreshed **by hand** every release — see § CI / Release; there is no post-hook yet.
> Historical release narrative lives in [`CHANGELOG.md`](CHANGELOG.md) (per-tag chronology).
> Doc-tree currency lives in [`docs/doc-health.md`](docs/doc-health.md) (fresh / stale / archive ledger).

This file (`CLAUDE.md`) is durable rules. See [first-party-documentation § CLAUDE.md](https://github.com/MacCracken/agnosticos/blob/main/docs/development/planning/first-party-documentation.md#claudemd) for what belongs where.

## Scaffolding

Project structure follows the first-party scaffold. Source files only need project-specific includes; stdlib + external deps resolve automatically from `cyrius.cyml`. Do not hand-roll root files — fix the scaffolder if it's missing something.

## Quick Start

```bash
cyrius build src/main.cyr build/agora        # build
./build/agora help                            # exercise dispatch
./build/agora version                         # version stamp
cyrius test                                   # unit tests: tests/agora.tcyr (modules) + tests/serve.tcyr (main.cyr's serve layer)
cyrius fuzz fuzz/telnet_iac.fcyr              # fuzz the IAC parser (also --poison=ab; both in CI + release)
cyrius fuzz fuzz/term_wrap.fcyr               # fuzz the word wrap egress text goes through (1.10.1; same gates)
docs/examples/run.sh [--model fork|poll] [NN] # the example smokes, each with the server it needs (CI runs both models)
benches/serve-bench.py all                    # accept rate, per-session memory, world-lock contention
scripts/check-version-sync.sh                 # VERSION vs cyrius.cyml / binary / CHANGELOG / state.md / roadmap
scripts/check-toolchain.sh                    # the local toolchain snapshot vs its cyrius tag (pre-cut)
cyrius audit                                  # fmt + lint + docs + tests + bench (a CI gate since 1.8.2)
./build/agora serve                           # start telnet listener; Ctrl-C exits cleanly (1.7.0)
```

## Key Principles

- **The wire is the contract** — RFC 854 and RFC 1184 are authoritative. Any deviation is a bug, not a feature. Cite section + line in code comments where behavior is subtle.
- **Cross-platform from M1** — the listener uses `lib/net.cyr` socket primitives, not raw syscalls. New platform support is a `lib/net.cyr` task, not an agora task.
- **Pure parsing is testable; socket I/O is wired** — keep the IAC/LINEMODE state machines side-effect-free so `tests/agora.tcyr` can exercise them without binding a port. (The serve layer itself is unit-tested over a socketpair in `tests/serve.tcyr` since 1.8.2.)
- **Posts are durable artifacts** — once written, a post is immutable from the protocol's perspective; there is no edit path today, and if one is added, edits become new revisions rather than in-place rewrites. Since 1.9.0 a post is published crash-safely — temp, fsync, `link(2)` into its id, directory fsync — so it is either absent or whole, and the id claim stays exclusive ([ADR 0025](docs/adr/0025-store-io-regular-files-and-publish.md), amending [ADR 0002](docs/adr/0002-one-file-per-post-storage.md)).
- **Admission control, not identity** — sigil gives us auth (M6); we are not a federated-identity system.
- Test after EVERY change, not after the feature is "done"
- ONE change at a time — never bundle unrelated changes
- **Build with `cyrius build`, never raw `cat file | cycc`** — the manifest auto-resolves deps and prepends includes
- Every buffer declaration is a contract: `var buf[N]` = N **bytes**, not N entries
- Fuzz every parser path — IAC sequences are adversarial-by-default (anyone with a telnet client can send them)

## Rules (Hard Constraints)

- **Read the genesis repo's CLAUDE.md first** — [agnosticos/CLAUDE.md](https://github.com/MacCracken/agnosticos/blob/main/CLAUDE.md)
- **Do not commit or push** — the user handles all git operations
- **NEVER use `gh` CLI** — use `curl` to the GitHub API if needed
- Do not add unnecessary dependencies. agora consumes named stdlib modules + sibling first-party crates (darshana, bannermanor, kii, sankoch, sigil) — nothing else.
- Do not validate against `gh pr` activity — validate against `cyrius test` and the RFC text.
- Do not skip tests before claiming changes work
- Do not use `sys_system()` with unsanitized input — every post field is external data
- Do not trust external data (telnet client bytes, file paths, post bodies) without validation
- Do not use `break` in while loops with `var` declarations — use flag + `continue`
- Do not add Cyrius stdlib includes in individual src files — the manifest resolves them
- Do not hardcode toolchain versions in CI YAML — the `cyrius = "X.Y.Z"` pin in `cyrius.cyml` is the only source of truth
- Do not inline the version number in CLAUDE.md or README — `VERSION` is the only source of truth

## Process

### P(-1): Hardening (before any new features, and at minor / v1.0 cuts)

1. **Cleanliness** — `cyrius build`, `cyrius lint`, `cyrius audit`; all tests pass
2. **Benchmark baseline** — `cyrius bench benches/bench_telnet.bcyr` (parser) + `benches/serve-bench.py all` (accept rate, per-session memory, world-lock contention), for comparison
3. **Internal deep review** — gaps, optimizations, correctness, docs
4. **External research** — re-read RFC 854 + RFC 1184; check against canonical telnet implementations (BSD telnetd, Linux net-tools)
5. **Security audit** — every IAC sequence path bounds-checked, no buffer overflows, no path traversal in post storage. File findings in `docs/audit/YYYY-MM-DD-audit.md`
6. **Additional tests / benchmarks** from findings
7. **Post-review benchmarks** — prove the wins against step 2
8. **Documentation audit** — ADRs for decisions made during hardening; update `docs/doc-health.md`
9. **Repeat if heavy** — keep drilling until clean

### Work Loop (continuous)

1. **Work phase** — new milestone bite, roadmap item, bug fix
2. **Build check** — `cyrius build src/main.cyr build/agora`
3. **Test + benchmark additions** for new code
4. **Internal review** — protocol-conformance, memory, correctness, edge cases
5. **Security check** — any new external-input path, buffer allocation, syscall usage
6. **Documentation** — update CHANGELOG, roadmap, `docs/development/state.md`, any ADR the change earned, refresh `docs/doc-health.md` row
7. **Version check** — `scripts/check-version-sync.sh` (VERSION is the only place to bump: the binary's strings come from `CYRIUS_PKG_VERSION` since 1.8.2)
8. **Return to step 1**

### Security Hardening (before every release)

Every project runs a security audit pass before release — see [first-party-standards § Security Hardening](https://github.com/MacCracken/agnosticos/blob/main/docs/development/planning/first-party-standards.md#security-hardening-new--required-before-every-release) for the full list. Minimum:

1. **Input validation** — every IAC option code, every subnegotiation payload, every post body bounds-checked
2. **Buffer safety** — every `var buf[N]` verified; N is **bytes**, max access < N, no adjacent-variable overflow
3. **Syscall review** — `lib/net.cyr` socket calls and `lib/fs.cyr` writes audited per release
4. **Pointer validation** — no raw pointer dereference of telnet bytes without bounds
5. **No command injection** — no `sys_system()` with post content; post bodies are inert data
6. **No path traversal** — board names / thread IDs / handles validated before any path is built, no `../` escape into the post tree
7. **Store opens refuse what is not a store file** — every store file goes through `store_open` (`store_read_all`, `store_lock_open`, `store_append_locked`): no final symlink, never blocks on a FIFO, regular files only. A plain `file_open` / `file_read_all` on a store path is a bug — a FIFO there hangs the whole poll server ([ADR 0025](docs/adr/0025-store-io-regular-files-and-publish.md)). Directories are listed only through `store_dir_scan`, which refuses a non-directory first (the stdlib's `dir_list_into` would block on a FIFO, 1.9.1)
8. **Known CVE review** — track BSD telnetd CVEs (CVE-2020-10188, CVE-2011-4862) and verify equivalent defenses
9. **Document findings** — all issues in `docs/audit/YYYY-MM-DD-audit.md`

Severity levels: **CRITICAL** (remote / privilege escalation), **HIGH** (moderate effort), **MEDIUM** (specific conditions), **LOW** (defense-in-depth).

### Closeout Pass (before every minor/major bump)

1. **Full test suite** — a bare `cyrius test`, zero failures: it runs every `tests/*.tcyr` — `tests/agora.tcyr` (the module suite; `src/test.cyr` until 1.8.2) and `tests/serve.tcyr` (main.cyr's serve layer, which includes `src/main.cyr` under `#define AGORA_TEST`). Also both fuzz harnesses — `cyrius fuzz fuzz/telnet_iac.fcyr` and `fuzz/term_wrap.fcyr` (1.10.1) — plain and `--poison=ab`, and the example smokes via `docs/examples/run.sh` (all CI + release gates since 1.8.2).
2. **Benchmark baseline** — `cyrius bench benches/bench_telnet.bcyr` + `benches/serve-bench.py all`; compare against the prior closeout in BENCHMARKS.md. **Run `scripts/check-toolchain.sh` first** — a dirty local toolchain snapshot once moved a measured binary by 215 KB
3. **Dead code audit** — remove unused functions; record remaining floor in CHANGELOG
4. **Refactor pass** — consolidate the minor's additions where parallel codepaths accreted
5. **Code review pass** — walk diffs end-to-end for missed guards, off-by-ones, silently-ignored errors
6. **Cleanup sweep** — stale comments, dead `#ifdef` branches, unused includes, orphaned files
7. **Security re-scan** — quick grep for new `sys_system`, unchecked writes, unsanitized input, buffer size mismatches, and any store path opened without `store_open` (`grep -n 'file_read_all\|file_open(' src/*.cyr` — outside `arena.cyr`'s primitives, the only plain opens left are `--motd`, the user's keyfile and `/dev/urandom`)
8. **Allocator gates** (added 1.6.6 — each is a mitigation an Accepted ADR relies on, and each existed only as a sentence inside that ADR until now):
   - **No bare `alloc()` on a per-line path reachable from `process_rx`** — per-line scratch belongs in the arena ([ADR 0021](docs/adr/0021-per-command-scratch-arena.md)); a bare `alloc()` on a dispatch path is an unbounded leak under `AGORA_SERVE=poll`. **⚠ A `src/`-only grep cannot enforce this.** The allocation may sit inside a *vendored stdlib* function you call: `dir_list` cost 4 KB/call until cyrius 6.5.11, and at 1.7.0 the stdlib's `file_write_atomic` was measured at 64 B/call and would have leaked on every chat `say` had agora not written `store_write_atomic` against the arena instead. **Read the allocations of any stdlib function you put on a per-line path** — at 1.8.1 `dir_list`/`str_from` (per listing), sigil's `hex_decode` (per `auth:`) and chrono's `iso8601_now` (per post) were all still leaking, unauthenticated and pipelinable (audit H1). Known deliberate exceptions: once-per-serve setup allocations, and process-lifetime buffers that grow only by doubling (the directory workspace, `store_dir_scan` in board.cyr). `descent_proxy`'s buffers were listed here as an exception until 1.8.1; they come from the arena now. Both halves of the 1.6.2 arena miss — the unauthenticated `scores` path and the chat idle tick — would have been caught here.
   - **The arena is a budget, not a free list** (added 1.8.1, audit H3). `cmd_alloc` falls back to a bare, never-reclaimed `alloc()` once a command has used `CMD_ARENA_BYTES` (512 KB) — so a helper that takes arena memory on EVERY call must never sit inside a per-post / per-user / per-entry loop. `post_read`'s 512-byte path, called once per post by `list`, spilled the arena on a ~1,500-post board and leaked ~400 KB per anonymous command. Per-iteration scratch goes on the stack (t232 pins the three loop helpers). **Prove a command bounded by measuring it** — a poll-mode heap A/B over a few thousand pipelined repetitions on a large store — not by reading `src/`; that is how both H1 and H3 were found.
   - **Mixed-allocator scan.** No `alloc()` pointer may reach `fl_free`, and no `fl_alloc()` pointer may be left for the arena ([ADR 0022](docs/adr/0022-door-state-free-hook.md) § Consequences). Check every game module's state constructor against its `*_free`.
   - **Deferral check, TREE-WIDE.** `cyrius lint` takes ONE file, so linting `main.cyr` alone under-reports: at 1.6.5 it said 2 while the tree had 12. Loop every `src/*.cyr`. Note the checker is per-line and treats any line mentioning `CHANGELOG` / `roadmap` / `docs/` / `issue` / `See ` as tracked — **citing a doc is not the same as being tracked in one**, so verify the cited entry actually exists.
9. **Downstream check** — none yet (agora has no consumers); will track at M5+ when other tools start scripting agora
10. **Doc sync** — CHANGELOG, roadmap, `docs/development/state.md`, `docs/doc-health.md`, CLAUDE.md (if durable content changed)
11. **Version verify** — `scripts/check-version-sync.sh --tag <intended tag>`: VERSION, cyrius.cyml, the binary, the CHANGELOG header, state.md's Released row and the roadmap's release row all agree (the release workflow runs the same check)
12. **Full build from clean** — `rm -rf build && cyrius deps && CYRIUS_DCE=1 cyrius build` passes clean, and `cyrius audit` exits 0 (fmt, lint, docs, tests, bench)

### Task Sizing

- **Low/Medium effort**: batch freely — multiple items per work loop cycle
- **Large effort**: small bites only — break into sub-tasks, verify each before moving to the next
- **If unsure**: treat it as large

### Refactoring Policy

- Refactor when the code tells you to — duplication, unclear boundaries, measured bottlenecks
- Never refactor speculatively. Wait for the third instance
- Every refactor must pass the same test + benchmark gates as new code
- 3 failed attempts = defer and document — don't burn time in a rabbit hole

## Cyrius Conventions

- All struct fields are 8 bytes (`i64`), accessed via `load64` / `store64` with offset
- Heap allocation via `fl_alloc()` / `fl_free()` (freelist) for data with individual lifetimes
- Bump allocation via `alloc()` for long-lived data (vec, str internals)
- Enum values for constants — don't consume `gvar_toks` slots (4,096 initialized globals limit)
- Counting rule (**widened by cyrius 6.4.74**): a top-level `var NAME = ...;` consumes an initialized-globals slot only when its initializer needs *runtime* evaluation — a call, or an identifier reference. Anything the constant folder can prove constant takes the static-init fast path and costs nothing: bare integer literals (`var x = 42;`), enum members, and — since 6.4.74's `_CF_TRY` folder — **foldable integer expressions** (`var x = 512 * 2;`, `var y = 1 << 4;`, `var z = (0 - 61);`). The folder is conservative and fail-safe: anything it cannot prove falls back to a deferred runtime store. Its precedence is **not C's** — `& | ^` sit in the `+ -` tier, left-associative, so `1 | 2 + 1` is `(1|2)+1`. See the cyrius guide's **Global Initializers** section (`docs/guides/cyrius-guide.md` in the cyrius repo)
- Heap-allocate large buffers — `var buf[256000]` bloats the binary by 256KB
- `break` in while loops with `var` declarations is unreliable — use flag + `continue`
- No negative literals — write `(0 - N)` not `-N`
- No mixed `&&` / `||` in one expression — nest `if` blocks instead
- `match` is reserved — don't use as a variable name
- `return;` without value is invalid — always `return 0;`
- All `var` declarations are function-scoped — no block scoping

## CI / Release

- **Toolchain pin**: `cyrius = "X.Y.Z"` field in `cyrius.cyml [package]`. No separate `.cyrius-toolchain` file.
- **Dead code elimination**: every `cyrius build` in CI and release runs with `CYRIUS_DCE=1`. Binary size is a release metric — track it in `state.md`.
- **Tag filter**: release workflow triggers on `tags: ['[0-9]*']` — semver-only.
- **Version**: `VERSION` is the only file a release bumps. `cyrius.cyml` reads it (`${file:VERSION}`) and the binary's banner / `--version` / MOTD read `CYRIUS_PKG_VERSION`, which `cyrius build` derives from the manifest (1.8.2 — they were three hand-edited literals).
- **Version-sync gate**: `scripts/check-version-sync.sh` runs on every CI push, and with `--tag` in the release workflow before anything is published: VERSION, cyrius.cyml, the built binary, the CHANGELOG header, `state.md`'s Released row and the roadmap's release row must agree.
- **State sync**: `docs/development/state.md` and `roadmap.md` are still refreshed **by hand** at every release — there is no post-hook (1.6.6 and 1.7.1 both shipped without either recording them) — but since 1.8.2 CI fails when they do not name `VERSION`, so the omission can no longer ship silently.
- **CI gates** (1.8.2): build (DCE), toolchain provenance (`--no-repo`), version sync, `cyrius test`, fuzz plain + `--poison=ab`, `cyrius audit`, the example smokes under BOTH serve models (`docs/examples/run.sh`), and an aarch64 build + test under qemu-user. The release workflow gates on all of it, then builds x86_64 / aarch64 / agnos binaries and publishes them with `SHA256SUMS`.
- **Supply chain**: the cyrius installer is fetched from the tag matching the pin, never `main`; GitHub actions are pinned by commit SHA; workflows default to `contents: read`.

## Docs

- [`docs/development/roadmap.md`](docs/development/roadmap.md) — milestones, sub-bites, v1.0 criteria.
- [`docs/development/state.md`](docs/development/state.md) — **live state snapshot, refreshed every release**.
- [`docs/doc-health.md`](docs/doc-health.md) — fresh / stale / archive / open-question ledger across the whole doc tree.
- [`docs/adr/`](docs/adr/) — architecture decision records. *Why did we choose X over Y?*
- [`docs/architecture/`](docs/architecture/) — non-obvious constraints and quirks. *What can't I derive from the code alone?*
- [`docs/guides/`](docs/guides/) — task-oriented how-tos.
- [`docs/examples/`](docs/examples/) — runnable examples.
- [`CHANGELOG.md`](CHANGELOG.md) — source of truth for all changes.

New quirks and constraints land in `docs/architecture/` as numbered items (`NNN-kebab-case.md`). New decisions land in `docs/adr/` using [`template.md`](docs/adr/template.md). **Never renumber either series.**

Full doc-tree convention: [first-party-documentation.md](https://github.com/MacCracken/agnosticos/blob/main/docs/development/planning/first-party-documentation.md).

## .gitignore (Required)

```gitignore
# Build
/build/
/dist/

# Resolved deps (auto-generated by cyrius deps) — NEVER commit these.
# The whole tree is regenerated from the pinned toolchain; a committed lib
# shadows the generated set and makes CI's `cyrius deps` fail on a bump.
# The old `!lib/k*.cyr` exception (it only ever matched the generated
# keccak.cyr) caused exactly that asymmetry and is gone — do not restore it.
cyrius.lock
lib/

# Release / toolchain artifacts
cyrius-*.tar.gz
*.tar.gz
SHA256SUMS

# IDE
.idea/
.vscode/
*.swp
*~

# OS
.DS_Store
Thumbs.db
```

## CHANGELOG Format

Follow [Keep a Changelog](https://keepachangelog.com/). Performance claims **must** include benchmark numbers. Breaking changes get a **Breaking** section with migration guide. Security fixes get a **Security** section with CVE references where applicable. See [first-party-documentation § CHANGELOG](https://github.com/MacCracken/agnosticos/blob/main/docs/development/planning/first-party-documentation.md#changelog) for the full conventions.
