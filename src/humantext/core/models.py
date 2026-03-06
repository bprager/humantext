"""Data models shared across analysis, rewrite, suggestion, and learning flows."""

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
    genre_note: str = ""

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
    genre: str | None = None
    profile_id: str | None = None
    profile_summary: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "summary": self.summary,
            "top_signals": self.top_signals,
            "mode": self.mode,
            "findings": [finding.to_dict() for finding in self.findings],
        }
        if self.genre is not None:
            payload["genre"] = self.genre
        if self.profile_id is not None:
            payload["profile_id"] = self.profile_id
        if self.profile_summary is not None:
            payload["profile_summary"] = self.profile_summary
        return payload


@dataclass(slots=True)
class EditPriority:
    signal_code: str
    goal: str
    strategy_code: str
    edit_scope: str
    risk_note: str
    span_text: str
    effective_score: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class EditSuggestion:
    edit_plan: list[EditPriority]
    sample_edits: list[dict[str, str]]
    analysis: AnalysisResult

    def to_dict(self) -> dict[str, Any]:
        return {
            "edit_plan": {"priorities": [priority.to_dict() for priority in self.edit_plan]},
            "sample_edits": self.sample_edits,
            "analysis": self.analysis.to_dict(),
        }


@dataclass(slots=True)
class VoiceTrait:
    trait_code: str
    trait_value: str
    confidence: float
    evidence_examples: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class VoiceProfile:
    profile_id: str
    author_id: str
    name: str
    profile_summary: str
    confidence: float
    corpus_doc_count: int
    traits: list[VoiceTrait]

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "author_id": self.author_id,
            "name": self.name,
            "profile_summary": self.profile_summary,
            "confidence": self.confidence,
            "corpus_doc_count": self.corpus_doc_count,
            "traits": [trait.to_dict() for trait in self.traits],
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
    change_log: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "output_text": self.output_text,
            "changes": [change.to_dict() for change in self.changes],
            "change_log": self.change_log,
            "warnings": self.warnings,
            "analysis": self.analysis.to_dict(),
        }
