"""Data models shared across analysis and rewrite flows."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class Finding:
    signal_code: str
    signal: str
    category: str
    description: str
    span_start: int
    span_end: int
    span_text: str
    severity: float
    confidence: float
    profile_adjustment: float = 0.0
    effective_score: float = 0.0
    evidence: list[str] = field(default_factory=list)
    rationale: str = ""
    recommended_strategies: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        if not self.effective_score:
            self.effective_score = round(self.severity + self.profile_adjustment, 3)
        return asdict(self)


@dataclass(slots=True)
class AnalysisResult:
    summary: str
    findings: list[Finding]
    top_signals: list[str]
    mode: str = "minimal"

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "top_signals": self.top_signals,
            "mode": self.mode,
            "findings": [finding.to_dict() for finding in self.findings],
        }


@dataclass(slots=True)
class RewriteChange:
    signal_code: str
    strategy: str
    before: str
    after: str
    rationale: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(slots=True)
class RewriteResult:
    output_text: str
    changes: list[RewriteChange]
    warnings: list[str]
    analysis: AnalysisResult

    def to_dict(self) -> dict[str, Any]:
        return {
            "output_text": self.output_text,
            "changes": [change.to_dict() for change in self.changes],
            "warnings": self.warnings,
            "analysis": self.analysis.to_dict(),
        }
