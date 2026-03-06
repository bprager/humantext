"""Minimal stdio MCP adapter for HumanText."""

from __future__ import annotations

import json
import sys
from typing import Any, TextIO

from humantext.core.analysis import analyze_text
from humantext.core.suggest import suggest_edits
from humantext.detectors.signals import SIGNALS
from humantext.rewrite.engine import rewrite_text
from humantext.storage.database import HumanTextDatabase
from humantext.version import get_version


DEFAULT_DB_PATH = "humantext.db"


def get_server_metadata() -> dict[str, Any]:
    """Return server metadata that can be reused by any MCP adapter."""
    return {
        "name": "humantext-mcp",
        "version": get_version(),
        "tools": [tool["name"] for tool in list_tools()],
    }


def list_tools() -> list[dict[str, Any]]:
    """Return the currently exposed MCP-style tool metadata."""
    return [
        {
            "name": "analyze_text",
            "description": "Analyze text for baseline stylistic signals.",
            "input": ["text", "genre?", "profile_id?", "mode?"],
        },
        {
            "name": "suggest_edits",
            "description": "Produce a ranked edit plan and sample edits.",
            "input": ["text", "genre?", "profile_id?", "mode?"],
        },
        {
            "name": "rewrite_text",
            "description": "Rewrite text using the currently implemented baseline strategies.",
            "input": ["text", "genre?", "profile_id?", "mode?"],
        },
        {
            "name": "learn_style",
            "description": "Learn and persist a voice profile from trusted documents.",
            "input": ["author_id", "documents[]", "name?", "db_path?"],
        },
        {
            "name": "get_voice_profile",
            "description": "Load a previously persisted voice profile.",
            "input": ["profile_id", "db_path?"],
        },
        {
            "name": "list_signals",
            "description": "List seeded baseline signal definitions.",
            "input": [],
        },
    ]


def handle_tool_call(tool_name: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Dispatch a tool call in-process."""
    params = params or {}
    mode = params.get("mode", "minimal")

    if tool_name == "analyze_text":
        result = analyze_text(params["text"], mode=mode).to_dict()
        if "genre" in params:
            result["genre"] = params["genre"]
        return result

    if tool_name == "suggest_edits":
        result = suggest_edits(params["text"], mode=mode).to_dict()
        if "genre" in params:
            result["genre"] = params["genre"]
        return result

    if tool_name == "rewrite_text":
        return rewrite_text(params["text"], mode=mode).to_dict()

    if tool_name == "learn_style":
        database = HumanTextDatabase(params.get("db_path", DEFAULT_DB_PATH))
        try:
            database.initialize()
            profile = database.learn_style(
                author_id=params["author_id"],
                documents=params.get("documents", []),
                profile_name=params.get("name"),
            )
        finally:
            database.close()
        return profile.to_dict()

    if tool_name == "get_voice_profile":
        database = HumanTextDatabase(params.get("db_path", DEFAULT_DB_PATH))
        try:
            database.initialize()
            profile = database.get_voice_profile(params["profile_id"])
        finally:
            database.close()
        if profile is None:
            return {"status": "not_found", "profile_id": params["profile_id"]}
        return profile.to_dict()

    if tool_name == "list_signals":
        return {
            "signals": [
                {
                    "signal_code": signal.code,
                    "name": signal.name,
                    "category": signal.category,
                    "description": signal.description,
                    "rewrite_strategies": list(signal.rewrite_strategies),
                }
                for signal in SIGNALS
            ]
        }

    raise KeyError(f"Unknown tool: {tool_name}")


def serve_stdio(instream: TextIO | None = None, outstream: TextIO | None = None) -> int:
    """Serve newline-delimited JSON requests over stdio."""
    instream = instream or sys.stdin
    outstream = outstream or sys.stdout

    for raw_line in instream:
        line = raw_line.strip()
        if not line:
            continue
        request = json.loads(line)
        request_id = request.get("id")
        if request.get("tool") == "server_metadata":
            response = {"id": request_id, "ok": True, "result": get_server_metadata()}
        else:
            try:
                result = handle_tool_call(request["tool"], request.get("params", {}))
                response = {"id": request_id, "ok": True, "result": result}
            except Exception as exc:  # pragma: no cover - defensive server boundary
                response = {"id": request_id, "ok": False, "error": str(exc)}
        outstream.write(json.dumps(response) + "\n")
        outstream.flush()
    return 0
