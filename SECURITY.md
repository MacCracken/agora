# Security Policy

## Reporting a Vulnerability

If you find a security issue in agora, **do not file a public issue or PR**. Email the maintainer privately at the address listed on the GitHub profile of the repo owner.

Include:

- A description of the issue and its impact.
- Reproducer — minimal code, telnet session transcript, or input bytes that trigger the bug.
- Versions affected (`agora` `VERSION` + `cyrius version`).
- Your suggested fix (optional but appreciated).

Expect an acknowledgement within 7 days. A fix lands in the next patch release, with the CVE (if any) referenced in the `Security` section of [`CHANGELOG.md`](CHANGELOG.md) and a per-audit writeup in `docs/audit/YYYY-MM-DD-audit.md`.

## Scope

In scope:

- Remote code execution via the telnet wire protocol (RFC 854 IAC parsing, RFC 1184 LINEMODE).
- Buffer overflows in the protocol parser, post storage, or auth code.
- Path traversal via board names, thread IDs, or post bodies (M5+).
- Authentication bypass against sigil-backed accounts (M6+).
- Privilege escalation via setuid bits or capability mishandling on platforms that ship them.
- Denial-of-service via malformed protocol sequences (any DOS that requires < 1 KB of input is in scope; > 1 KB is judgment-call).

Out of scope:

- Plaintext telnet traffic on the open internet — telnet *is* plaintext by RFC. Use a TLS terminator (stunnel, sslh) in front for hostile network paths. agora 1.x does not bundle TLS.
- Resource exhaustion from legitimate-shape traffic (many simultaneous connections) — that's a tuning problem, not a vulnerability.
- Vulnerabilities in Cyrius stdlib (`lib/net.cyr`, `lib/fs.cyr`, etc.) — report those to the [cyrius repo](https://github.com/MacCracken/cyrius). We'll bump our pin once the fix ships.
- Vulnerabilities in AGNOS kernel (when agora runs on AGNOS) — report those to the [agnos repo](https://github.com/MacCracken/agnos).

## Security audit cadence

Per [`CLAUDE.md` § Security Hardening](CLAUDE.md#security-hardening-before-every-release), every release runs a security pass. Audit findings file in `docs/audit/YYYY-MM-DD-audit.md`. Three audits are on file — [2026-05-23](docs/audit/2026-05-23-audit.md), [2026-06-15](docs/audit/2026-06-15-audit.md) and [2026-07-26](docs/audit/2026-07-26-audit.md) — with every HIGH, MEDIUM and LOW finding discharged as of 1.6.5.

**Dynamic analysis** landed at **1.7.0**: `fuzz/telnet_iac.fcyr` drives the RFC 854 / 1143 / 1073 / 1091 / 1184 IAC parser — the most exposed surface agora has, reachable pre-authentication by anyone who can open a TCP connection — and asserts its own bounds invariants. It runs in CI on every push and again at release, and it is mutation-proven: removing the `TERMINAL_TYPE` clamp (the CVE-2020-10188 shape) or the subnegotiation accumulator bound each turns it red. Prior to 1.7.0 the 2026-07-26 audit recorded, correctly, that agora had **no dynamic analysis at all**.

## Known CVE-equivalent prior art we defend against

- **CVE-2020-10188** (NetKit telnetd) — buffer overflow in `nextitem()` IAC option parsing. agora's IAC parser bounds-checks every option-length read.
- **CVE-2011-4862** (BSD telnetd `encrypt_keyid`) — stack overflow in the Authentication option subnegotiation. agora does not implement the Authentication option; auth is handled at the application layer via sigil.
