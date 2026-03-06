"""Baseline text analysis helpers."""

from __future__ import annotations

import re
from collections import Counter

from humantext.core.models import AnalysisResult, Finding
from humantext.detectors.signals import SIGNALS


def analyze_text(text: str, mode: str = "minimal") -> AnalysisResult:
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
                    )
                )

    findings.sort(key=lambda item: (-item.effective_score, item.span_start, item.signal_code))
    counts = Counter(finding.signal_code for finding in findings)
    top_signals = [signal_code for signal_code, _ in counts.most_common(5)]
    summary = _build_summary(findings)
    return AnalysisResult(summary=summary, findings=findings, top_signals=top_signals, mode=mode)


def _build_summary(findings: list[Finding]) -> str:
    if not findings:
        return "No baseline signals detected in the current draft."

    categories = Counter(finding.category for finding in findings)
    dominant = ", ".join(category for category, _ in categories.most_common(2))
    return f"Detected {len(findings)} baseline signal(s), concentrated in {dominant}."
