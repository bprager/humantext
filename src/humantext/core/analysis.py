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
) -> AnalysisResult:
    """Return baseline signal findings with spans and rewrite strategies."""
    findings: list[Finding] = []
    for signal in SIGNALS:
        for pattern in signal.patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
                span_text = match.group(0)
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
                        effective_score=signal.severity_default,
                        evidence=[span_text],
                        rationale=signal.rationale,
                        recommended_strategies=list(signal.rewrite_strategies),
                        genre_note=_build_genre_note(signal.category, genre),
                    )
                )

    findings.sort(key=lambda item: (-item.effective_score, item.span_start, item.signal_code))
    counts = Counter(finding.signal_code for finding in findings)
    top_signals = [signal_code for signal_code, _ in counts.most_common(5)]
    summary = _build_summary(findings, genre=genre, profile_summary=profile_summary)
    return AnalysisResult(
        summary=summary,
        findings=findings,
        top_signals=top_signals,
        mode=mode,
        genre=genre,
        profile_id=profile_id,
        profile_summary=profile_summary,
    )


def _build_summary(findings: list[Finding], *, genre: str | None = None, profile_summary: str | None = None) -> str:
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
