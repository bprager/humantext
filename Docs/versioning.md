# Versioning

## Decision

HumanText uses a single tracked version source: `src/humantext/VERSION`.

Everything else derives from that file:

- Python package metadata
- `humantext version`
- any future server `/version` endpoint or MCP metadata response
- `humantext.mcp.get_server_metadata()` responses
- GitHub release tags
- `Changelog.md` release sections

## Rules

1. The canonical version is stored once in `src/humantext/VERSION`.
2. Runtime code must call `humantext.version.get_version()` instead of hardcoding version strings.
3. Git tags for releases must be `vX.Y.Z` and must match `src/humantext/VERSION` exactly.
4. `Changelog.md` must keep an `[Unreleased]` section at the top.
5. Tagged releases must have a matching topmost numbered changelog section, for example `## [0.1.3]`.
6. GitHub Releases are created only from validated tags.
7. Any server surface that reports a version must use the same runtime helper as the CLI.

## Enforcement

- `scripts/check_version_sync.py` verifies that the package version, CLI version, and changelog structure match.
- In CI release runs, the same script compares the current package version against `GITHUB_REF_NAME` and requires a matching topmost release section in `Changelog.md`.
- `.github/workflows/release.yml` blocks release creation if the tag, runtime version, or changelog release section diverge.

## Operational flow

1. Run `python scripts/prepare_release.py X.Y.Z` or `make release-prep VERSION=X.Y.Z`.
2. Review the updated `src/humantext/VERSION` and `Changelog.md`.
3. Create tag `vX.Y.Z`, or rerun the helper with `--tag`.
4. Push the commit and tag.
5. GitHub Actions validates `make check`, changelog structure, and version alignment, then creates the release.

## Why this model

This is simpler and more auditable than duplicating version strings across Python metadata, CLI output, servers, and release notes. It keeps local development predictable while still enforcing release consistency automatically.

## Helper

- `scripts/prepare_release.py X.Y.Z` updates `src/humantext/VERSION` and moves the current `[Unreleased]` notes into a new top release section.
- `scripts/prepare_release.py X.Y.Z --tag` also creates `git tag vX.Y.Z`.
- `make release-prep VERSION=X.Y.Z` is a thin wrapper around the same script.
