<!-- markdownlint-disable MD024 -->
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Changed

- Promoted the Python package scaffold from `Docs/` to the repository root and standardized the repo layout around `src/`, `Docs/`, `migrations/`, and `tests/`.
- Replaced the placeholder migration with the relational-first schema described in the project documentation.
- Refreshed the repository `README.md` for GitHub with clearer positioning, a tighter feature summary, and the project inspiration reference.

### Added

- Root `Makefile` with `test` and `check` targets.
- Minimal unit and CLI smoke tests for the scaffold implementation.
- Root `.gitignore` coverage for local Codex files, Python caches, virtualenvs, and archive artifacts.
- Missing `.codex` control files required by the project bootstrap instructions.

---

## [0.1.0] – Initial

### Added

- Initial project structure

---
