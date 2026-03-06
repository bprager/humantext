"""Minimal MCP-style metadata surface for HumanText."""

from __future__ import annotations

from typing import Any

from humantext.version import get_version


def get_server_metadata() -> dict[str, Any]:
    """Return server metadata that can be reused by any MCP adapter."""
    return {
        "name": "humantext-mcp",
        "version": get_version(),
        "tools": [
            "analyze_text",
            "suggest_edits",
            "rewrite_text",
            "learn_style",
        ],
    }
