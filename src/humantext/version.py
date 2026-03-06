"""Single-source version helpers for HumanText."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version as package_version
from pathlib import Path


_VERSION_FILE = Path(__file__).with_name("VERSION")


def get_version() -> str:
    """Return the canonical HumanText version.

    Installed distributions report their package metadata version.
    Source checkouts fall back to the tracked VERSION file.
    """
    try:
        return package_version("humantext")
    except PackageNotFoundError:
        return _VERSION_FILE.read_text(encoding="utf-8").strip()


__version__ = get_version()
