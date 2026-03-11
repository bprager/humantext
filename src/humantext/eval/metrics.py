"""Evaluation metric helpers."""

from __future__ import annotations

from difflib import SequenceMatcher

from humantext.rewrite.guardrails import negations, protected_tokens, qualifiers


def edit_distance_ratio(original: str, rewritten: str) -> float:
    """Return a normalized edit distance ratio using sequence similarity."""
    return round(1.0 - SequenceMatcher(a=original, b=rewritten).ratio(), 3)


def protected_token_metrics(original: str, rewritten: str) -> tuple[float, list[str]]:
    required = protected_tokens(original)
    observed = protected_tokens(rewritten)
    return _retention_from_sets(required, observed)


def qualifier_metrics(original: str, rewritten: str) -> tuple[float, list[str]]:
    required = qualifiers(original)
    observed = qualifiers(rewritten)
    return _retention_from_sets(required, observed)


def negation_metrics(original: str, rewritten: str) -> tuple[float, list[str]]:
    required = negations(original)
    observed = negations(rewritten)
    return _retention_from_sets(required, observed)


def expected_token_metrics(expected_tokens: tuple[str, ...], rewritten: str) -> tuple[float, list[str]]:
    if not expected_tokens:
        return 1.0, []
    missing = [token for token in expected_tokens if token not in rewritten]
    kept = len(expected_tokens) - len(missing)
    return round(kept / len(expected_tokens), 3), missing


def _retention_from_sets(required: set[str], observed: set[str]) -> tuple[float, list[str]]:
    if not required:
        return 1.0, []
    missing = sorted(required - observed)
    kept = len(required) - len(missing)
    return round(kept / len(required), 3), missing
