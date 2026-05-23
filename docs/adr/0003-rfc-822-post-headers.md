# 0003 — RFC-822-shaped post headers (Subject + Date)

> **Status**: Accepted
> **Date**: 2026-05-23

## Context

[ADR 0002](0002-one-file-per-post-storage.md) deferred the question of post metadata: M5-A shipped plaintext-body-only posts because we didn't know what fields the wire-level post flow needed. After M5-A/B/C/H landed and `agora` is a working BBS over the wire, the gap is sharp: `list` displays bare integer IDs, so a user reading `1, 2, 3` has to `read` every post to find what they want. Every BBS in the 35-year history of the format displays *something* per post in the list — at minimum a subject line, usually also an author and a date.

This ADR picks the header format that lets `list` look like a BBS instead of a numbered file dump.

Three candidate shapes for the per-post metadata block:

- **(A) RFC-822-shaped headers** — `Subject: foo\r\n\r\nbody`. Same shape every email + Usenet message has used since 1982. Parser is "first uppercase letter? then scan for blank line; body starts after."
- **(B) JSON header line** — `{"subject":"foo","date":"..."}\n\nbody`. Programmatic-friendly but breaks the "any Unix tool reads it" property from ADR 0002.
- **(C) CYML / TOML front matter** — `+++\nsubject = "foo"\n+++\n\nbody`. Matches the cyrius-ecosystem manifest format (the agora repo's `cyrius.cyml` is one already). Adds a new fence syntax to teach users.
- **(D) Tab-separated single header line** — `Subject\tDate\tbody...`. Compact but fragile (tabs in subjects break it; no extensibility).

## Decision

**(A) — RFC-822-shaped headers**. Post file format:

```
Subject: <single-line UTF-8, no CR/LF in value>
Date: <ISO-8601 UTC: YYYY-MM-DDTHH:MM:SSZ>

<body bytes — anything except NUL and ESC per M5-H ingress filter>
```

Specific choices:

- **Header block ends at the first blank line** — `\r\n\r\n` or `\n\n` (mixed acceptable). Body starts immediately after.
- **Headers are name-colon-space-value-CRLF**. Names are ASCII letters + dashes; values are UTF-8 single-line.
- **Subject and Date are the v1.0 header set.** Subject is user-supplied at post time; Date is server-generated via `chrono.iso8601_now()`. Author lands at M6 when sigil-backed identity is real; `Reply-To` lands at M5-F when threading lands; further extensions earn their own bites + ADR updates.
- **Backwards compat with M5-A/B/C posts** — files that don't start with an ASCII uppercase letter are treated as headerless: body is the whole file, Subject + Date are empty. No migration step; old posts keep working.
- **Header sniffer is conservative**. The first byte of the file must be an ASCII uppercase letter (`A`-`Z`, byte range 65-90) for any header parsing to engage. Lowercase / digit / punctuation first byte → no headers, whole file is body. This means a post body that happens to start with the word `Subject:` (no leading-uppercase ambiguity) won't be misinterpreted as a header — the file is treated as headerless body.

## Consequences

**Positive**:

- **BBS-shaped `list` output.** `list` shows `<id>  <subject>` per row instead of bare IDs. Users can scan for what they want without reading every post.
- **Familiar to anyone who's used a Unix-shaped system.** Email, Usenet, mbox, HTTP, MIME, and even Markdown front matter trace back to the RFC-822 shape. No new mental model.
- **Extensible without breaking older readers.** A future bite can add `Reply-To`, `From`, `In-Reply-To`, `Tags` — old code that only knows `Subject` + `Date` just ignores unknown headers and still finds the body offset correctly.
- **Body-offset detection is O(n) single-pass.** Scan for `\n\n` or `\r\n\r\n`; if found, body is past it; if not, body is the whole file. No state machine, no precedence rules.
- **Trivial Unix-tool inspection.** `head post.txt` shows headers + first body lines. `grep -l Subject:.*hello posts/*.txt` finds matching posts. `awk '/^$/{flag=1; next} flag' post.txt` extracts the body. Standard tooling works.
- **The interop story continues to graduate cleanly into v2.x.** Pillar 2 (content-addressing) hashes the canonical post file — headers are part of the canonical form. Pillar 4 (federation by topic) and pillar 6 (store-and-forward) both want headers (topic ID, message ID, signature) without breaking the body-after-blank-line shape.

**Negative**:

- **Parser tolerance is a known surface.** Real RFC-822 parsers handle header continuation (`\r\n\t...`), comments, multi-value headers, encoded-words. Our v1.0 parser does none of that — it reads single-line `Name: value\r\n` headers only. If a future header needs continuation (e.g. very long `In-Reply-To` chains), we'll either chunk it or grow the parser.
- **Posts now have a per-file size floor of ~40 bytes** (`Subject: \r\nDate: 2026-05-23T12:30:00Z\r\n\r\n` is ~38 bytes). Negligible vs. post-body content, but technically the inode-pressure concern from ADR 0002 § Negative consequences gets slightly worse.
- **Subject is single-line.** Multi-line subjects (which RFC 822 allows via continuation) are out — the typed Subject prompt is a single line of input. Operators of high-art-BBS deployments who want ASCII-art subject lines will get cropped to the first line.
- **No header validation at write time.** A future bite could enforce "Subject is non-empty" / "Date format is exactly ISO-8601" / etc. — but M5-D writes what it gets and trusts the in-session prompt to be sane (M5-H input filter already drops the dangerous bytes).

**Neutral**:

- **Backwards-compat with headerless posts works forever**, but the canonical-form for the content-addressing graduation (pillar 2) will pick a fixed shape; old headerless posts will hash to a different content ID than they would after a forward-migration. That's expected and survives the v2.x cut.

## Alternatives considered

**(B) JSON header line.** Rejected. Wins on machine-readability but loses the "any Unix text tool inspects it" property that ADR 0002 § Positive consequences leans on. JSON also doesn't extend gracefully — adding fields is fine; removing them silently breaks readers. RFC-822's parse-known-ignore-unknown is the better extensibility model.

**(C) CYML / TOML front matter.** Rejected for M5-D. The fence syntax (`+++` or similar) is a new dialect we'd teach users — and the only consumer of richer-typed-headers (lists, nested maps) is a hypothetical future M5+. RFC-822 is sufficient for `Subject` (string) + `Date` (string) + later `From` (string) + `Reply-To` (string). If a future header genuinely needs nested structure, we can either inline a serialized blob in a single header value or revisit the format at the v2.x cut.

**(D) Tab-separated single header line.** Rejected. Fragile (tab characters in subjects are real; quoting rules invite their own bugs), un-extensible (adding a field shifts all later fields), and unfamiliar (no other text-protocol uses TSV headers). The compactness win doesn't earn its keep.

**No headers at all — Subject in a sidecar index file.** Rejected. Adds a two-file invariant (post + index must stay consistent — exactly the failure mode ADR 0002 § Alternatives rejected for the same reason at the storage-layout level). Headers-in-the-file keeps the post file as the single source of truth.

**Headers in CLI `agora post`'s argv (`--subject "foo"`)** alongside the in-session Subject prompt. **Accepted** — CLI flag is the natural shape for piped / scripted post creation; in-session prompt is the natural shape for interactive use. Both write the same on-disk format.
