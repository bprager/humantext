"""Baseline text analysis helpers."""

from __future__ import annotations

import re
from collections import Counter

from humantext.core.models import AnalysisResult, Finding
from humantext.detectors.signals import SIGNALS


def analyze_text(
    text: str,
    mode: str = "minimal",
    *,
    genre: str | None = None,
    profile_id: str | None = None,
    profile_summary: str | None = None,
    profile_traits: dict[str, str] | None = None,
) -> AnalysisResult:
    """Return baseline signal findings with spans and rewrite strategies."""
    findings: list[Finding] = []
    normalized_traits = _normalize_profile_traits(profile_traits)
    for signal in SIGNALS:
        for pattern in signal.patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
                span_text = match.group(0)
                profile_adjustment = _profile_adjustment(signal.code, signal.category, normalized_traits)
                effective_score = _bounded_score(signal.severity_default + profile_adjustment)
                findings.append(
                    Finding(
                        signal_code=signal.code,
                        signal=signal.name,
                        category=signal.category,
                        description=signal.description,
                        span_start=match.start(),
                        span_end=match.end(),
                        span_text=span_text,
                        severity=signal.severity_default,
                        confidence=signal.confidence,
                        profile_adjustment=profile_adjustment,
                        effective_score=effective_score,
                        evidence=[span_text],
                        rationale=signal.rationale,
                        recommended_strategies=list(signal.rewrite_strategies),
                        genre_note=_build_genre_note(signal.category, genre),
                    )
                )

    findings.sort(key=lambda item: (-item.effective_score, item.span_start, item.signal_code))
    counts = Counter(finding.signal_code for finding in findings)
    top_signals = [signal_code for signal_code, _ in counts.most_common(5)]
    summary = _build_summary(findings, genre=genre, profile_summary=profile_summary, profile_traits=normalized_traits)
    return AnalysisResult(
        summary=summary,
        findings=findings,
        top_signals=top_signals,
        mode=mode,
        genre=genre,
        profile_id=profile_id,
        profile_summary=profile_summary,
    )


def _build_summary(
    findings: list[Finding],
    *,
    genre: str | None = None,
    profile_summary: str | None = None,
    profile_traits: dict[str, str] | None = None,
) -> str:
    if not findings:
        summary = "No baseline signals detected in the current draft."
    else:
        categories = Counter(finding.category for finding in findings)
        dominant = ", ".join(category for category, _ in categories.most_common(2))
        summary = f"Detected {len(findings)} baseline signal(s), concentrated in {dominant}."

    notes: list[str] = []
    if genre:
        notes.append(f"Reviewed as {genre}.")
    if profile_summary:
        notes.append("Voice profile context loaded.")
    if profile_traits:
        adjusted = sum(1 for finding in findings if finding.profile_adjustment != 0)
        if adjusted:
            notes.append(f"Profile-aware scoring adjusted {adjusted} finding(s).")
    if not notes:
        return summary
    return f"{summary} {' '.join(notes)}"


def _build_genre_note(category: str, genre: str | None) -> str:
    if not genre:
        return ""

    normalized = genre.strip().lower()
    if category in {"structure", "formatting"}:
        return f"This pattern can be normal in {normalized} writing when the structure is deliberate."
    if category == "style":
        return f"This wording can be genre-typical in {normalized} writing, so compare it against house style before editing."
    if category == "citations":
        return f"In {normalized} writing, citation-like phrasing should still point to a verifiable source."
    if category == "chat_residue":
        return f"In {normalized} writing, assistant-style residue is usually still out of place."
    return f"In {normalized} writing, keep the signal only if it matches the intended editorial voice."


def _normalize_profile_traits(profile_traits: dict[str, str] | None) -> dict[str, str]:
    if not profile_traits:
        return {}
    return {str(code).strip().lower(): str(value).strip().lower() for code, value in profile_traits.items()}


def _profile_adjustment(signal_code: str, category: str, traits: dict[str, str]) -> float:
    if not traits:
        return 0.0

    tolerance = traits.get("tolerance_for_abstraction")
    directness = traits.get("directness")
    transition_rate = _safe_float(traits.get("transition_frequency"))

    adjustment = 0.0
    abstraction_signals = {
        "ABSTRACT_NOUN_OVERUSE",
        "BROADER_TRENDS_PADDING",
        "LEGACY_LANGUAGE",
        "GENERIC_SIGNIFICANCE",
    }

    if signal_code in abstraction_signals:
        if tolerance == "high":
            adjustment -= 0.18
        elif tolerance == "medium":
            adjustment -= 0.08
        elif tolerance == "low":
            adjustment += 0.08

    if signal_code in {"CANNED_TRANSITION_ADDITIONALLY", "CANNED_TRANSITION_OVERALL"}:
        if transition_rate >= 0.12:
            adjustment -= 0.1
        elif transition_rate <= 0.04:
            adjustment += 0.05

    if signal_code in {"VAGUE_ATTRIBUTION", "WEASEL_GENERALIZATION"}:
        if directness == "direct":
            adjustment += 0.08
        elif directness == "measured":
            adjustment -= 0.05

    if category == "chat_residue":
        adjustment += 0.1

    return round(adjustment, 3)


def _safe_float(value: str | None) -> float:
    if value is None:
        return 0.0
    try:
        return float(value)
    except ValueError:
        return 0.0


def _bounded_score(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 3)
