"""Minimal stdio MCP adapter for HumanText."""

from __future__ import annotations

import json
import sys
from typing import Any, TextIO

from humantext.core.analysis import analyze_text
from humantext.detectors.signals import SIGNALS
from humantext.rewrite.engine import rewrite_text
from humantext.version import get_version


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
            "description": "Produce a minimal ranked edit plan from current findings.",
            "input": ["text", "genre?", "profile_id?", "mode?"],
        },
        {
            "name": "rewrite_text",
            "description": "Rewrite text using the currently implemented baseline strategies.",
            "input": ["text", "genre?", "profile_id?", "mode?"],
        },
        {
            "name": "learn_style",
            "description": "Reserved endpoint for future voice-profile learning.",
            "input": ["author_id", "documents[]"],
        },
        {
            "name": "get_voice_profile",
            "description": "Reserved endpoint for future voice-profile retrieval.",
            "input": ["profile_id"],
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
        analysis = analyze_text(params["text"], mode=mode)
        priorities = []
        for finding in analysis.findings:
            strategy = finding.recommended_strategies[0] if finding.recommended_strategies else "review"
            priorities.append(
                {
                    "signal_code": finding.signal_code,
                    "goal": finding.description,
                    "strategy_code": strategy,
                    "edit_scope": "local",
                    "risk_note": "Review manually if domain-specific nuance matters.",
                }
            )
        return {"edit_plan": {"priorities": priorities}, "sample_edits": []}

    if tool_name == "rewrite_text":
        return rewrite_text(params["text"], mode=mode).to_dict()

    if tool_name == "learn_style":
        return {
            "status": "not_implemented",
            "author_id": params.get("author_id"),
            "documents": len(params.get("documents", [])),
        }

    if tool_name == "get_voice_profile":
        return {"status": "not_implemented", "profile_id": params.get("profile_id")}

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
