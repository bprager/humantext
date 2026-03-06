"""Validate version alignment across source, CLI, release tags, and changelog."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
CHANGELOG = ROOT / "Changelog.md"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from humantext.version import get_version

_CHANGELOG_HEADER_RE = re.compile(r"^## \[(?P<name>[^\]]+)\]", re.MULTILINE)
_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def _normalize_tag(tag: str) -> str:
    return tag[1:] if tag.startswith("v") else tag


def _load_changelog_headers() -> list[str]:
    if not CHANGELOG.exists():
        raise SystemExit("Changelog.md is missing")
    return [match.group("name") for match in _CHANGELOG_HEADER_RE.finditer(CHANGELOG.read_text(encoding="utf-8"))]


def _validate_changelog_structure(headers: list[str]) -> list[str]:
    if not headers or headers[0] != "Unreleased":
        raise SystemExit("Changelog.md must start with an [Unreleased] section")
    return [header for header in headers if _SEMVER_RE.match(header)]


def _validate_release_changelog(expected_version: str, release_headers: list[str]) -> None:
    if expected_version not in release_headers:
        raise SystemExit(f"Changelog mismatch: missing section for [{expected_version}]")
    if not release_headers or release_headers[0] != expected_version:
        raise SystemExit(
            f"Changelog mismatch: latest release section is [{release_headers[0] if release_headers else 'none'}], expected [{expected_version}]"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Check HumanText version synchronization")
    parser.add_argument("--expected-tag", help="Git tag or release name to compare against")
    args = parser.parse_args()

    version = get_version()
    cli = subprocess.run(
        [sys.executable, "-m", "humantext.cli.main", "version"],
        cwd=ROOT,
        env={"PYTHONPATH": str(SRC)},
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    if cli != version:
        raise SystemExit(f"CLI version mismatch: cli={cli} package={version}")

    changelog_headers = _load_changelog_headers()
    release_headers = _validate_changelog_structure(changelog_headers)

    if args.expected_tag:
        expected = _normalize_tag(args.expected_tag)
        if expected != version:
            raise SystemExit(f"Release tag mismatch: tag={expected} package={version}")
        _validate_release_changelog(expected, release_headers)

    print(version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
