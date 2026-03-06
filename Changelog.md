<!-- markdownlint-disable MD024 -->
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

_No unreleased changes._

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
