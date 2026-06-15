# 001 — Cyrius `callptr` / indirect-call constraints

> **Affects**: `src/main.cyr` door descriptor registry ([ADR 0020](../adr/0020-door-descriptor-registry.md)); any future fn-pointer / vtable dispatch.

Two non-obvious constraints surfaced building the 1.4.6 door descriptor registry
(`callptr` through a heap table of `&fn` addresses). Neither is documented in the
cyrius guide; both cost real debugging time. Recorded so the next person doesn't
re-derive them.

## 1. `callptr` results must be bound — a bare `callptr(...)` statement does not parse

`callptr(fp, args...)` is valid only in **value position** — `return callptr(...)`
or `x = callptr(...)`. As a bare expression statement (result discarded) it does
**not** parse: the compiler emits `expected var, got '('`, and — critically — it
reports the error at a **cascaded, misleading line** (the start of a *later*
function), not at the offending `callptr`. During the registry work this sent the
reported error wandering through several already-correct functions while the real
fault sat in a `door_world_begin` / `door_universe_feed` tick/notice call whose
return value we did not need.

**Rule**: even when you don't want the result, bind it:

```
if (tfp != 0) { var tr = callptr(tfp, world, turn); }   # tr unused, but required
```

(The same does **not** apply to ordinary calls — `ash_world_tick(...)` as a bare
statement is fine. It is specific to the `callptr` builtin.)

A secondary, related gotcha: a `callptr` **argument** that is itself a nested call
or compound expression (`callptr(fp, load64(p))`, `callptr(fp, a / b)`) is
fragile — hoist it to a local first (`var x = load64(p); callptr(fp, x)`). Ordinary
builtins like `store64`/`memcpy` accept nested-call args fine; `callptr` is the
picky one.

## 2. `0` is a valid struct-field offset — don't use it as the "absent" sentinel

The descriptor stores byte-offsets into a game's state struct (e.g. where to write
the session fp). The first field of a struct is at **offset 0** — and one really
is: `AE_FP = 0` (Ashes stores the player fp in its first field). A `0`-means-none
sentinel therefore silently skips a legitimate offset-0 write. Ashes founded every
player as fp `0` and the smoke caught it ("not founded a home province"); Port
(fp field at a non-zero offset) passed, masking the bug.

**Rule**: for an *optional offset* where 0 is a valid value, store **`offset + 1`**
and subtract on use (`0` = none). The descriptor's `DD_FP_OFF` uses this bias.
(Offsets that are only read when a *companion* fp is non-zero — e.g. `DD_TICK_NS`,
read only when `DD_WORLD_TICK != 0` — don't need the bias.)
