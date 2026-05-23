# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.1.0] — 2026-05-23 (Scaffold)

### Added

- Repo scaffold: `VERSION`, `cyrius.cyml` (toolchain pin 6.0.1), `src/main.cyr` (argv dispatch + boot banner + stub verbs), `README.md` (etymology + roadmap), `CHANGELOG.md`, `LICENSE` (GPL-3.0-only), `.gitignore`.
- Six stub verbs: `serve` (M1 telnet listener), `post` / `list` / `read` (M5 persistence), `whoami` (M6 auth), `version`, `help`.
- Build verified: `cyrius build src/main.cyr build/agora` → 43,216 B binary; `./build/agora help` + `version` exercise the dispatch.

### Notes

- Pre-M1 release — no networking, no persistence, no protocol code. Verbs print stubs and exit non-zero (except `version` / `help`).
- M1 (telnet listener) is gated on agnos 1.32.2 cycle closing — `tcp_listen(23)` must validate end-to-end on archaemenid iron first.
- M5 (post persistence) is gated on agnos 1.33.x ext4 WRITE landing (Phase 1-5 currently read-only).
- Naming convention: introduces a Greek lane to the AGNOS ecosystem alongside the existing Sanskrit/Hindi (system libs) + English-wordplay / Polynesian (user-facing tools) lanes — see [[feedback_naming_lanes]]. The name threads three independent layers — ancient Greek ἀγορά + Doja Cat "Agora Hills" (Scarlet, 2023) + Agoura Hills CA (literally adjacent to the project's home base in Thousand Oaks). Multi-layer convergence in the spirit of `kii`'s Polynesian/East-Asian/English-phonetic precedent.
