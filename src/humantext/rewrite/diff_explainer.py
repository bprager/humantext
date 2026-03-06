"""Reviewer-friendly change explanations for rewrite output."""

from __future__ import annotations

from humantext.core.models import RewriteChange


def build_change_log(changes: list[RewriteChange], *, limit: int = 160) -> list[dict[str, str]]:
    """Return concise, reviewable explanations for rewrite changes."""
    entries: list[dict[str, str]] = []
    seen: set[tuple[str, str, str, str, str]] = set()
    for change in changes:
        before = _clip(change.before, limit=limit)
        after = _clip(change.after, limit=limit)
        key = (change.signal_code, change.strategy, change.rationale, before, after)
        if key in seen:
            continue
        seen.add(key)
        entries.append(
            {
                "signal_code": change.signal_code,
                "strategy_code": change.strategy,
                "explanation": change.rationale,
                "before": before,
                "after": after,
            }
        )
    return entries


def _clip(text: str, *, limit: int) -> str:
    text = " ".join(text.strip().split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."
