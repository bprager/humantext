<!-- markdownlint-disable MD024 -->
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

_No unreleased changes._

## [0.2.0] - 2026-03-11

### Changed

- Added profile-aware finding scoring so analysis now adjusts severity by learned traits such as abstraction tolerance, transition frequency, and directness.
- Threaded persisted voice traits through CLI, MCP, suggestion, and rewrite flows so profile context affects prioritization, not just summary text.
- Expanded project documentation with a technical runtime overview, an optional LLM integration investigation, and a roadmap that now includes broader detector coverage, span-targeted rewriting, and optional LLM augmentation.
- Added a shared rewrite-guardrail helper layer so LLM rewrite safety checks and evaluation metrics use the same preservation rules.

### Added

- Added optional LLM scaffolding with an OpenAI-compatible adapter and first-pass span-level rewrite support for flagged sentences.
- Added CLI and MCP configuration paths for user-defined optional LLM rewrite settings.
- Added `.env` and environment-based defaults for optional LLM configuration, with explicit CLI and MCP inputs taking precedence.
- Added deterministic post-checks for LLM rewrites and a second-pass critique stage that can combine residual signal analysis with optional LLM review.
- Added a critique-driven second LLM rewrite pass for remaining flagged spans after the first rewrite.
- Added an `eval` package, a `humantext eval` CLI command, markdown report rendering, and a seeded `data/datasets/core-v1` benchmark corpus.

### Tests

- Added assertions that profile context produces non-zero `profile_adjustment` values in API, CLI, and MCP analysis paths.
- Added evaluation-runner and CLI coverage for the seeded benchmark dataset and markdown report output.

## [0.1.3] - 2026-03-06

### Changed

- Added `genre` and `profile_id` plumbing to the CLI, analysis layer, rewrite layer, and MCP adapter so contract-level context now flows through the runtime.
- Added per-finding `genre_note` output and rewrite `change_log` explanations to align runtime JSON more closely with the agent design in `AGENTS.md`.
- Reworked top-level README badges so release appears once, plus explicit lint/test and code coverage badges.
- Hardened the release workflow for tagged releases with tag validation, clearer release naming, and idempotent release publication settings.
- Added a coverage gate to `make coverage` with `COVERAGE_MIN=90` as the default threshold.

### Added

- Added a dedicated CI workflow (`.github/workflows/ci.yml`) to run lint, tests, and coverage reporting on pushes and pull requests.
- Added a one-click backfill workflow (`.github/workflows/backfill-releases.yml`) to convert existing semantic version tags into GitHub Releases.
- Added a pull request template with explicit checks for tests, changelog updates, and version/release hygiene.

### Tests

- Added coverage for genre/profile-aware analysis output and reviewer-facing rewrite change logs across the Python API, CLI, and MCP adapter.

## [0.1.2] - 2026-03-06

### Changed

- Added a real `suggest_edits` service with ranked priorities and sample rewrites.
- Added baseline voice-profile learning with SQLite persistence for authors, profiles, and traits.
- Added a stdio MCP adapter with tool dispatch and shared version metadata for local agent/editor integration.
- Added sentence polishing after rewrite strategy application so rewritten output recovers cleaner sentence starts.

## [0.1.1] - 2026-03-06

### Changed

- Added rewrite coverage for `GENERIC_SIGNIFICANCE`, `BROADER_TRENDS_PADDING`, and `VAGUE_ATTRIBUTION`, reducing unresolved high-value warnings.
- Promoted the Python package scaffold from `Docs/` to the repository root and standardized the repo layout around `src/`, `Docs/`, `migrations/`, and `tests/`.
- Replaced the placeholder migration with the relational-first schema described in the project documentation.
- Refreshed the repository `README.md` for GitHub with clearer positioning, a tighter feature summary, and the project inspiration reference.

### Added

- Added `humantext.mcp.get_server_metadata()` so server and MCP metadata report the shared runtime version.
- Single-source versioning via `src/humantext/VERSION`, a CLI `version` command, and release synchronization checks for GitHub tags and `Changelog.md`.
- `scripts/prepare_release.py` and `make release-prep VERSION=X.Y.Z` to update `src/humantext/VERSION` and create the matching top release section in `Changelog.md`.
- Root `Makefile` with `test` and `check` targets.
- Minimal unit and CLI smoke tests for the scaffold implementation.
- Root `.gitignore` coverage for local Codex files, Python caches, virtualenvs, and archive artifacts.
- Missing `.codex` control files required by the project bootstrap instructions.

---

## [0.1.0] – Initial

### Added

- Initial project structure

---
