# 002 — `cyrius lib sync` silently skips same-size stdlib files

> ## ✅ FIXED UPSTREAM AT cyrius 6.5.7 — agora has been clear since the 1.6.7 pin (6.5.33; now 6.5.34)
>
> `_dep_copy_file` no longer returns early on equal size. Size is now a **negative fast path only**
> (different size ⇒ definitely copy); equal size falls through to `_files_identical`, a byte compare —
> deliberately a byte compare rather than `_sha256sum_file`, which would fork ~99 processes per sync and
> make a core correctness predicate depend on an external binary. Verified two ways at the 1.6.7 cut:
> bisected across every `6.5.*` tag (`_files_identical` first appears in `cbt/deps.cyr` at **6.5.7**,
> absent at 6.5.6), and **mutation-tested on this repo** — flipping one byte in a comment of
> `lib/net.cyr`, preserving its exact length, then running plain `cyrius lib sync` (not even `--full`)
> repaired the file. Under 6.4.78 that mutation survived.
>
> **This note is kept, not retired.** Three reasons: a downgrade below 6.5.7 re-arms the trap; the
> vintage table below is the record of what the 1.6.0 and 1.6.1 binaries were actually built against;
> and § Detection's `cmp` sweep is now the cheap *verification* that the fix is working, which is how
> 1.6.7 caught something else entirely — the local `6.5.33` snapshot was a **dirty working tree**, two
> libs and `cycc` off-tag. **The sweep found real drift at this cut too; it was just upstream of the
> tool rather than inside it.** § The procedure step 4 stays; only its rationale changes, from
> "the copier lies" to "the snapshot may not be what it claims".
>
> **§ Blast radius is corrected**: CI was never exposed. `ci.yml` and `release.yml` run `cyrius deps`
> into a fresh checkout where `lib/` is gitignored and therefore empty, and the skip required a
> pre-existing same-size destination. The exposure was always local-workstation only.
>
> The *"`copied N files` is a lie of omission"* paragraph below **remains true** — `cbt/commands.cyr`
> still increments its counter unconditionally, so the printed count is still files *considered*, not
> files *written*.

> **Affects**: every toolchain-pin bump in this repo (`cyrius.cyml [package].cyrius` + `cyrius lib sync --full`). Surfaced at the 1.6.1 cut (6.4.32 → 6.4.78), which found **six** vendored `lib/*.cyr` still carrying content from *earlier* pins — four of them stale since the 1.6.0 cut's 6.2.8 → 6.4.32 sync.

## The trap

`cyrius lib sync --full` reports `copied 99 .cyr files (full snapshot)` — and the
count is a lie of omission. It counts files *considered*, not files *written*.
The copy itself short-circuits on a size comparison (`cbt/deps.cyr`
`_dep_copy_file`):

```
# Skip if destination exists and same size (already resolved)
var src_sz = _file_size(src);
var dst_sz = _file_size(dst);
if (src_sz > 0 && src_sz == dst_sz) { return 2; }
```

That heuristic is correct for its original job (re-resolving an unchanged git
dep) and wrong for a toolchain bump, because **a stdlib module very often
changes without changing its byte count**. The common case is the generated
`dist` header:

```
# niyama.cyr -- bundled distribution
# Version: 1.0.5      <-- becomes 1.0.6: same length, same file size
```

Any edit whose net length delta is zero — a version stamp, a renamed
same-length identifier, a reflowed comment — is invisible to the size check.
The sync prints success, the pin says the new toolchain, and `lib/` keeps
serving the old bytes indefinitely: nothing in a later sync will ever
reconsider the file, because the sizes still match.

## How it showed up at 1.6.1

Six files survived `lib sync --full` unchanged, in two vintages:

| File | Vendored content was from | Went stale at |
|---|---|---|
| `pam.cyr`, `regression.cyr`, `shadow.cyr`, `ws.cyr` | the **6.2.8** snapshot | the 1.6.0 cut (6.2.8 → 6.4.32) |
| `niyama.cyr` (1.0.5 → 1.0.6) | 6.2.8 / 6.4.32 (identical there) | this cut (6.4.32 → 6.4.78) |
| `yantra.cyr` (1.0.0 → 1.0.1) | the **6.4.32** snapshot | this cut |

So the 1.6.0 release built against a `lib/` that was 6.4.32 *except* for four
modules it never noticed were 6.2.8-era.

## Detection

Two signals, neither sufficient alone:

1. **The driver warning (partial).** The `cyrius` driver — not `cycc`; a raw `cycc` invocation never sees the manifest — emits, at ≥ 6.4.7x,
   `warning: ./lib/ shadows version-pinned ~/.cyrius/versions/<pin>/lib — N bundled lib(s) differ`
   and names them. It caught `niyama` and `yantra` here — but only because those
   two carry a parseable `# Version:` stamp. The other four (`pam`,
   `regression`, `shadow`, `ws`) are plain stdlib modules with no version line
   and went unreported.

2. **A `cmp` sweep (authoritative).** Compare every file byte-for-byte against
   the pinned snapshot:

   ```bash
   for f in ~/.cyrius/versions/$(grep '^cyrius' cyrius.cyml | cut -d'"' -f2)/lib/*.cyr; do
       b=$(basename "$f"); cmp -s "$f" "lib/$b" || echo "STALE: $b"
   done
   ```

## The procedure

After **every** pin bump, in this order:

1. Edit `cyrius.cyml [package].cyrius`.
2. `cyrius lib sync --full`
3. `cyrius deps` (resolves the git deps; does **not** touch stdlib files)
4. Run the `cmp` sweep above and `cp -f` any file it names from
   `~/.cyrius/versions/<pin>/lib/` into `lib/`.
5. Re-run the sweep — it must print nothing — then build.

**For pins < 6.5.7**, step 4 was not optional and could not be replaced by
re-running step 2: a second `lib sync` made exactly the same size comparison and
skipped exactly the same files. **At ≥ 6.5.7 the copier is correct**, so step 4 is
now a cheap *verification* rather than a repair — keep it anyway. It is what
caught, at 1.6.7, that the local `6.5.33` snapshot was not the released tag at all
(see the banner at the top): the copier was doing its job faithfully and copying
the wrong bytes.

## Blast radius when it goes unnoticed

At 1.6.1 the refresh was inert — the DCE binary was the same size before and
after (14,567,408 B), and 221/221 tests plus the full example-smoke suite were
green either way, because agora links none of the six modules on a hot path.
That is luck, not a guarantee: `lib/` is `.gitignore`d in full, so a stale
vendored module leaves **no trace in the repo** and no diff to review. The
failure mode it sets up is a silent, unreproducible divergence between what CI
builds (a clean `cyrius deps` into an empty `lib/` — always current) and what
the developer builds locally (whatever survived the last skip).

## See also

- [`001-cyrius-callptr-constraints.md`](001-cyrius-callptr-constraints.md) — the other undocumented-toolchain-behavior note.
- `cbt/deps.cyr` `_dep_copy_file` and `cbt/commands.cyr` `cmd_lib_sync` in the cyrius repo — the two functions that produce this behavior.
