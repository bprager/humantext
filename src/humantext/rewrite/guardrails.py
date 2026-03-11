"""Shared rewrite guardrail helpers."""

from __future__ import annotations

import re


def post_check_rewrite(original: str, candidate: str) -> list[str]:
    """Return any guardrail violations detected in a rewritten span."""
    issues: list[str] = []
    if not candidate or not candidate.strip():
        return ["candidate is empty"]
    if len(candidate) > max(len(original) * 3, len(original) + 80):
        issues.append("candidate expands the sentence too aggressively")
    if len(candidate) < max(5, len(original) // 4):
        issues.append("candidate removes too much content")

    for token in protected_tokens(original):
        if token not in protected_tokens(candidate):
            issues.append(f"missing protected token: {token}")

    for qualifier in qualifiers(original):
        if qualifier not in qualifiers(candidate):
            issues.append(f"dropped qualifier: {qualifier}")

    for negation in negations(original):
        if negation not in negations(candidate):
            issues.append(f"dropped negation: {negation}")

    added_entities = _suspicious_added_entities(original, candidate)
    if added_entities:
        issues.append(f"introduced new capitalized entity: {', '.join(sorted(added_entities))}")
    return issues


def protected_tokens(text: str) -> set[str]:
    """Collect tokens that should survive conservative rewrites."""
    tokens = set(re.findall(r"\b\d+(?:\.\d+)?\b", text))
    tokens.update(re.findall(r"https?://[^\s]+", text))
    tokens.update(re.findall(r"\b[A-Z]{2,}\b", text))
    return tokens


def qualifiers(text: str) -> set[str]:
    """Collect hedge and qualifier terms that often matter semantically."""
    lowered = text.lower()
    candidates = {
        "may",
        "might",
        "could",
        "about",
        "around",
        "approximately",
        "roughly",
        "some",
        "several",
        "often",
        "sometimes",
    }
    return {qualifier for qualifier in candidates if re.search(rf"\b{re.escape(qualifier)}\b", lowered)}


def negations(text: str) -> set[str]:
    """Collect explicit negation terms that should be preserved."""
    lowered = text.lower()
    candidates = {"not", "no", "never", "without", "none"}
    return {negation for negation in candidates if re.search(rf"\b{re.escape(negation)}\b", lowered)}


def _suspicious_added_entities(original: str, candidate: str) -> set[str]:
    original_entities = _capitalized_entities(original)
    candidate_entities = _capitalized_entities(candidate)
    blacklist = {"This", "That", "These", "Those", "The", "A", "An", "Keep"}
    return {entity for entity in candidate_entities - original_entities if entity not in blacklist}


def _capitalized_entities(text: str) -> set[str]:
    return set(re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", text))
