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

> Volatile state lives in [`docs/development/state.md`](docs/development/state.md) — current version, binary size, in-flight slot, recent releases, consumer status, gate state for downstream milestones. Refreshed every release (ideally bumped by the release post-hook).
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
cyrius test src/test.cyr                      # unit tests (parser, IAC sequences)
./build/agora serve                           # start telnet listener (M1)
```

## Key Principles

- **The wire is the contract** — RFC 854 and RFC 1184 are authoritative. Any deviation is a bug, not a feature. Cite section + line in code comments where behavior is subtle.
- **Cross-platform from M1** — the listener uses `lib/net.cyr` socket primitives, not raw syscalls. New platform support is a `lib/net.cyr` task, not an agora task.
- **Pure parsing is testable; socket I/O is wired** — keep the IAC/LINEMODE state machines side-effect-free so `src/test.cyr` can exercise them without binding a port.
- **Posts are durable artifacts** — once written, a post is immutable from the protocol's perspective. Edits are new revisions (M4 delta-stored).
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
- Do not let M5 (post persistence) gate M1–M4 — protocol code is reachable today, persistence is the last unlock

## Process

### P(-1): Hardening (before any new features, and at minor / v1.0 cuts)

1. **Cleanliness** — `cyrius build`, `cyrius lint`, `cyrius audit`; all tests pass
2. **Benchmark baseline** — capture parser throughput + accept-loop rate for comparison
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
7. **Version check** — `VERSION`, `cyrius.cyml`, CHANGELOG header in sync
8. **Return to step 1**

### Security Hardening (before every release)

Every project runs a security audit pass before release — see [first-party-standards § Security Hardening](https://github.com/MacCracken/agnosticos/blob/main/docs/development/planning/first-party-standards.md#security-hardening-new--required-before-every-release) for the full list. Minimum:

1. **Input validation** — every IAC option code, every subnegotiation payload, every post body bounds-checked
2. **Buffer safety** — every `var buf[N]` verified; N is **bytes**, max access < N, no adjacent-variable overflow
3. **Syscall review** — `lib/net.cyr` socket calls and `lib/fs.cyr` writes audited per release
4. **Pointer validation** — no raw pointer dereference of telnet bytes without bounds
5. **No command injection** — no `sys_system()` with post content; post bodies are inert data
6. **No path traversal** — board names / thread IDs validated, no `../` escape into the post tree
7. **Known CVE review** — track BSD telnetd CVEs (CVE-2020-10188, CVE-2011-4862) and verify equivalent defenses
8. **Document findings** — all issues in `docs/audit/YYYY-MM-DD-audit.md`

Severity levels: **CRITICAL** (remote / privilege escalation), **HIGH** (moderate effort), **MEDIUM** (specific conditions), **LOW** (defense-in-depth).

### Closeout Pass (before every minor/major bump)

1. **Full test suite** — all `.tcyr` pass, zero failures
2. **Benchmark baseline** — capture parser throughput + accept rate; compare against prior closeout
3. **Dead code audit** — remove unused functions; record remaining floor in CHANGELOG
4. **Refactor pass** — consolidate the minor's additions where parallel codepaths accreted
5. **Code review pass** — walk diffs end-to-end for missed guards, off-by-ones, silently-ignored errors
6. **Cleanup sweep** — stale comments, dead `#ifdef` branches, unused includes, orphaned files
7. **Security re-scan** — quick grep for new `sys_system`, unchecked writes, unsanitized input, buffer size mismatches
8. **Downstream check** — none yet (agora has no consumers); will track at M5+ when other tools start scripting agora
9. **Doc sync** — CHANGELOG, roadmap, `docs/development/state.md`, `docs/doc-health.md`, CLAUDE.md (if durable content changed)
10. **Version verify** — `VERSION`, `cyrius.cyml`, CHANGELOG header, intended git tag all match
11. **Full build from clean** — `rm -rf build && cyrius deps && CYRIUS_DCE=1 cyrius build` passes clean

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
- Enum values for constants — don't consume `gvar_toks` slots (256 initialized globals limit)
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
- **Version-verify gate**: release asserts `VERSION == cyrius.cyml version == git tag` before building.
- **State sync**: release post-hook bumps `docs/development/state.md`. If the hook doesn't, fix the hook — don't hand-maintain state.

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

# Resolved deps (auto-generated by cyrius deps)
lib/*.cyr
!lib/k*.cyr

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
