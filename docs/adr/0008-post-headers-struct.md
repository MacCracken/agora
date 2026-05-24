# 0008 — Post header parameters as a struct (pre-1.0 ABI shape)

> **Status**: Accepted
> **Date**: 2026-05-23

## Context

The post-creation API surface has grown twice during the M5–M6 cycles, and the v1.x roadmap (federation, content-addressed storage) credibly forecasts at least two more growths:

| Bite | Function | Arity | Added |
|---|---|---|---|
| M5-D | `post_format_with_subject(subject, body, body_len, out_buf, out_cap)` | 5 | Subject |
| M5-F | `post_format_with_headers(subject, reply_to, body, body_len, out_buf, out_cap)` | 6 | Reply-To |
| M6-E | `post_format_with_headers(subject, reply_to, from_handle, from_fp, body, body_len, out_buf, out_cap)` | **8** | From handle + From fp |
| (forecast) | + `origin` for federated peers (per ADR 0006 § Negative) | 9 | Origin |
| (forecast) | + `content_hash` for content-addressed storage (v2.x pillar 2) | 10 | Content-Hash |

Same growth on `post_new_with_subject_reply` (currently 8 args). Each new header is one more positional arg, which:

1. Punishes call sites — every caller updates whether or not they use the new field.
2. Encourages `0` / `null` padding at every call site for fields you don't care about (already visible in `post_format_with_subject` → `post_format_with_headers(subject, 0, 0, 0, body, body_len, out_buf, out_cap)`).
3. Loses argument identity at the call boundary — `post_format_with_headers("subj", 42, "alice", "deadbeef", ...)` requires the reader to count positions and remember which slot is the handle vs the fingerprint vs the parent-id.

The 1.0 release is the moment to lock the public surface. Whatever shape we pick now stays through 1.x without breakage. Two viable shapes for the freeze:

1. **(A) Freeze the 8-arg signature as-is.** Future headers earn either new variant fns (`post_format_with_origin`) or get ad-hoc-stuffed into the subject text. Zero refactor cost today.
2. **(B) Refactor to a `PostHeaders` parameter struct.** One struct ptr plus body / out / cap = 5 args. Future headers add a new `PH_*` enum offset + one setter; call sites that don't use the new field don't change. Medium refactor cost today.

### Forces

- **Cyrius struct ergonomics**: the codebase already uses the struct-via-i64-offsets pattern (`TS_*` for `TelnetState`, `STAT_MODE` / `STAT_BUFSZ` for stat results, `BoardPolicy` enum + path builders). Adding `PH_*` is idiomatic, not a new convention.
- **CLAUDE.md "third instance" rule**: the signature has grown three times (M5-D, M5-F, M6-E). The refactor is earned.
- **Caller surface is small**: 4 production call sites (`cmd_post` × 1, `session_finalize_post` × 2, `post_format_with_headers` internal recursion) + 4 test call sites (t49, t64, t65, t66). Total impact bounded at ~8 lines changed per shape.
- **Backwards-compat is not load-bearing pre-1.0**: per CLAUDE.md "Avoid backwards-compatibility hacks". The shim wrappers (`post_format_with_subject`, `post_new_with_subject`) added at M5-F / M6-E for "smooth out-of-cycle adoption" are themselves dead — every internal caller went straight to the full-arg variant by M6-F. Their continued existence is rot.

## Decision

**(B)** — refactor to a `PostHeaders` parameter struct ahead of the 1.0 ABI freeze. Replace the two 8-arg variant fns with single-pointer-arg fns:

```
post_format(ph, body, body_len, out_buf, out_cap)        # 5 args
post_new(store, board, ph, body, body_len)               # 5 args
```

The struct lives in `src/board.cyr` alongside the other ADR-0002 / 0003 / 0005 / 0006 post-storage primitives, follows the existing i64-offset convention:

```
enum PH {
    PH_SUBJECT     = 0;     # cstring ptr or 0 for empty
    PH_REPLY_TO    = 8;     # i64 parent ID; 0 means "not a reply"
    PH_FROM_HANDLE = 16;    # cstring ptr or 0 for anonymous
    PH_FROM_FP     = 24;    # cstring ptr or 0 for anonymous (paired with FROM_HANDLE)
    PH_SIZE        = 32;
}
```

Constructor + setters:

```
post_headers_new()                                  → ph (zero-initialized)
post_headers_set_subject(ph, subject_cstr)
post_headers_set_reply_to(ph, parent_id)
post_headers_set_from(ph, handle_cstr, fp_cstr)    # both nullable; null pair → anonymous
```

**In scope**: the two formatter/writer fns replaced; struct + constructor + 3 setters added; all 4 production call sites + 4 test call sites updated; the now-dead `post_format_with_subject` and `post_new_with_subject` shim wrappers removed (no production caller; removing them is CLAUDE.md "delete unused" hygiene, not breakage).

**Out of scope**: any header that isn't currently in the 8-arg shape. Future ADRs add new `PH_*` fields + setters as those features land; the call-shape stays constant.

## Consequences

### Positive

- **ABI freeze achievable.** The struct shape is the public surface. Adding a new `PH_*` field is a private change (new offset, new setter, no caller break). Existing callers continue to compile and link unchanged. The 1.0 promise becomes credible.
- **Call-site readability.** `post_headers_set_from(ph, "alice", "deadbeef12345678")` reads field-name-with-value; `post_format_with_headers("subj", 42, "alice", "deadbeef12345678", ...)` requires position-counting.
- **No `0` padding at call sites** that don't use optional fields. Anonymous posts construct just a Subject-set `ph` and pass it; today they pass `(subject, 0, 0, 0, body, ...)`.
- **Tests stay terse.** `var ph = post_headers_new(); post_headers_set_subject(ph, "subj"); post_headers_set_reply_to(ph, 42);` is two more lines per test than the inline-args shape but each line is self-documenting; the test-doc-cost amortises.
- **Future federation / content-addr fields are free** at the call-shape level. `post_headers_set_origin(ph, origin_cstr)` ships in a v1.x bite without touching any existing caller.

### Negative

- **One-time refactor across 8 call sites.** Bounded; landed in the same bite as the decision.
- **Backwards-compat-shim removal is a Breaking change** per Keep a Changelog. The shims (`post_format_with_subject`, `post_new_with_subject`) are documented in CHANGELOG [0.9.0] § Breaking — though no external consumer exists today (agora is a binary, not a library), so the impact surface is limited to anyone who patched against the M5 surface and didn't update through M6.
- **Slight allocation cost per post** — one extra `alloc(32)` per `post_headers_new` call. Per CLAUDE.md memory model (`alloc()` is bump-only), this is the same shape as every other per-call allocation in `handle_client`; ADR 0007's fork-per-conn reclaims it at child `sys_exit` so there's no long-running-process leak.

### Neutral

- **Header read path unchanged.** `header_get` / `post_subject` / `post_reply_to` / `post_from` all parse the wire format, not the construction args. The 0.7.0 H3 fix (re-validating handle/fp in `post_from`) is in the read path and stays intact.
- **The 0.7.0 H1 fix** (`header_text_cstr_ok` validation of `--subject` in `cmd_post`) runs on the cstring before it's stored in `ph`'s subject slot. Validation point unchanged.

## Alternatives considered

- **(A) Freeze 8-arg shape and accept variant-fn growth**: rejected because every future header earns either a new public function name (`post_format_with_origin`, `post_format_with_content_hash`, ...) or an ad-hoc encoding into the subject field (worse). At 1.x scale we'd be shipping a `post_format_v3` by year-end. Pre-1.0 pain (this refactor) is strictly less than the post-1.0 pain (perpetual variant proliferation).
- **(C) Refactor to a flat heap-buffer + offset table** (like RFC 822 itself — caller passes a pre-formatted header block): rejected because that pushes formatting up to every caller, defeating the whole point of having a formatter primitive. The caller would now need to know about Date / Reply-To / From line ordering + CRLF conventions.
- **(D) Variadic / tagged params (i.e., a `(key, value, key, value, …)` stream)**: rejected because cyrius doesn't have varargs and emulating it via fixed-size key/value arrays adds a parser step inside `post_format` for no readability win over the struct shape.
- **(E) Keep the shims (`post_format_with_subject`, `post_new_with_subject`) alongside the new struct API**: rejected per CLAUDE.md "Avoid backwards-compatibility hacks". The shims have zero production callers as of 0.8.3; deletion is hygiene.

## Specifics

- **Field semantics** (same as the pre-refactor 8-arg shape; only the call shape changes):
  - `PH_SUBJECT == 0` → no Subject line (the current "`subject == 0 || strlen(subject) == 0`" branch in `post_format_with_headers`).
  - `PH_REPLY_TO == 0` → no Reply-To line.
  - `PH_FROM_HANDLE == 0` OR `PH_FROM_FP == 0` → no From line (anonymous post; current "`from_handle != 0 && from_fp != 0`" pair-check stays).
- **No serialization change.** The wire / on-disk format is unchanged — `post_format`'s output is byte-identical to the pre-refactor `post_format_with_headers` for any equivalent input. The 0.4.x → 0.8.x stores keep reading; new posts written under 0.9.0 keep being readable by 0.8.x readers.
- **Shim removal is one bite with the refactor.** `post_format_with_subject` and `post_new_with_subject` deleted in the same patch that introduces the struct. CHANGELOG flags this under `### Breaking` so anyone who patched against the M5 surface notices.
- **No new tests for the shape itself.** Existing t49 / t64 / t65 / t66 cover the format semantics and are updated to the new call shape — passing tests prove the wire output is identical.

## Followups

- **v1.x federation** — `post_headers_set_origin(ph, origin_cstr)` lands as a single new offset + setter when the v2.x pillar 1 work earns it. ADR 0006 § Negative.
- **v2.x content-addressed storage** — `post_headers_set_content_hash(ph, hash_cstr)` likewise.
- **ABI versioning policy** — `PH_SIZE` growing is a forward-compatible change at the call-shape level but a recompilation requirement for binary consumers. Not relevant for agora (binary, not library), but worth noting if a future MUD-userland-companion repo ever links against `lib/board.cyr` directly.
