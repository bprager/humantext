"""Prepare a HumanText release by synchronizing VERSION and Changelog.md."""

from __future__ import annotations

import argparse
import re
import subprocess
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "src" / "humantext" / "VERSION"
CHANGELOG = ROOT / "Changelog.md"
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
UNRELEASED_RE = re.compile(
    r"(?P<header>## \[Unreleased\]\n\n)(?P<body>.*?)(?=^## \[)",
    re.DOTALL | re.MULTILINE,
)
RELEASE_HEADER_RE = re.compile(r"^## \[(?P<version>[^\]]+)\]", re.MULTILINE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare a HumanText release")
    parser.add_argument("version", help="Semantic version to release, for example 0.1.1")
    parser.add_argument("--tag", action="store_true", help="Create git tag vX.Y.Z after updating files")
    return parser.parse_args()


def validate_version(version: str) -> None:
    if not SEMVER_RE.match(version):
        raise SystemExit(f"Invalid semantic version: {version}")


def load_changelog() -> str:
    if not CHANGELOG.exists():
        raise SystemExit("Changelog.md is missing")
    return CHANGELOG.read_text(encoding="utf-8")


def extract_unreleased_body(changelog: str) -> tuple[re.Match[str], str]:
    match = UNRELEASED_RE.search(changelog)
    if not match:
        raise SystemExit("Could not locate the [Unreleased] section in Changelog.md")
    body = match.group("body").strip()
    if not body or body == "_No unreleased changes._":
        raise SystemExit("Refusing to prepare a release with an empty [Unreleased] section")
    return match, body


def ensure_release_does_not_exist(changelog: str, version: str) -> None:
    versions = [match.group("version") for match in RELEASE_HEADER_RE.finditer(changelog)]
    if version in versions:
        raise SystemExit(f"Changelog already contains a release section for [{version}]")


def rewrite_changelog(changelog: str, version: str, body: str, match: re.Match[str]) -> str:
    released_on = date.today().isoformat()
    replacement = (
        f"{match.group('header')}_No unreleased changes._\n\n"
        f"## [{version}] - {released_on}\n\n"
        f"{body}\n\n"
    )
    return changelog[: match.start()] + replacement + changelog[match.end() :]


def write_release_files(version: str) -> None:
    changelog = load_changelog()
    ensure_release_does_not_exist(changelog, version)
    match, body = extract_unreleased_body(changelog)
    VERSION_FILE.write_text(f"{version}\n", encoding="utf-8")
    CHANGELOG.write_text(rewrite_changelog(changelog, version, body, match), encoding="utf-8")


def create_tag(version: str) -> None:
    subprocess.run(["git", "tag", f"v{version}"], cwd=ROOT, check=True)


def main() -> int:
    args = parse_args()
    validate_version(args.version)
    write_release_files(args.version)
    if args.tag:
        create_tag(args.version)
    print(args.version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
