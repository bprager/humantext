"""Span-level LLM rewrite helpers."""

from __future__ import annotations

from dataclasses import dataclass

from humantext.core.models import Finding, RewriteCritiqueItem
from humantext.core.segmentation import Span, sentence_spans
from humantext.llm.client import LLMClient
from humantext.llm.config import LLMConfig
from humantext.rewrite.guardrails import post_check_rewrite


@dataclass(frozen=True, slots=True)
class SpanRewrite:
    sentence: Span
    findings: tuple[Finding, ...]


def rewrite_flagged_spans(
    text: str,
    findings: list[Finding],
    *,
    mode: str,
    profile_summary: str | None,
    config: LLMConfig,
    client: LLMClient,
    extra_instructions: list[str] | None = None,
    critique_items: list[RewriteCritiqueItem] | None = None,
) -> tuple[str, list[dict[str, str]], list[str]]:
    """Rewrite only sentences overlapped by findings."""
    rewrites = _collect_span_rewrites(text, findings)
    updated = text
    changes: list[dict[str, str]] = []
    warnings: list[str] = []

    for rewrite in reversed(rewrites):
        original = updated[rewrite.sentence.start_offset:rewrite.sentence.end_offset]
        instructions = _build_instructions(
            rewrite.findings,
            mode=mode,
            profile_summary=profile_summary,
            extra_instructions=_sentence_instructions(
                rewrite.sentence,
                critique_items=critique_items,
                extra_instructions=extra_instructions,
            ),
        )
        try:
            candidate = client.rewrite_span(sentence=original, instructions=instructions)
        except Exception as exc:
            warnings.append(f"LLM span rewrite failed for sentence {rewrite.sentence.ordinal}: {exc}")
            continue
        if not _is_safe_rewrite(original, candidate):
            warnings.append(f"Rejected unsafe LLM rewrite for sentence {rewrite.sentence.ordinal}.")
            continue
        if candidate == original:
            continue
        updated = updated[: rewrite.sentence.start_offset] + candidate + updated[rewrite.sentence.end_offset :]
        changes.append(
            {
                "before": original,
                "after": candidate,
                "signal_codes": ", ".join(sorted({finding.signal_code for finding in rewrite.findings})),
                "rationale": "Applied optional LLM rewrite to the flagged sentence span.",
            }
        )
    return updated, changes, warnings


def _collect_span_rewrites(text: str, findings: list[Finding]) -> list[SpanRewrite]:
    rewrites: list[SpanRewrite] = []
    for sentence in sentence_spans(text):
        overlapping = [
            finding
            for finding in findings
            if finding.span_start < sentence.end_offset and finding.span_end > sentence.start_offset
        ]
        if overlapping:
            rewrites.append(SpanRewrite(sentence=sentence, findings=tuple(overlapping)))
    return rewrites


def _build_instructions(
    findings: tuple[Finding, ...],
    *,
    mode: str,
    profile_summary: str | None,
    extra_instructions: list[str] | None = None,
) -> str:
    goals = "; ".join(sorted({finding.description for finding in findings}))
    signal_codes = ", ".join(sorted({finding.signal_code for finding in findings}))
    notes = [f"Mode: {mode}.", f"Signals to address: {signal_codes}.", f"Goals: {goals}."]
    if profile_summary:
        notes.append(f"Voice profile summary: {profile_summary}")
    if extra_instructions:
        notes.append(f"Additional critique to address: {' '.join(extra_instructions[:3])}")
    notes.append("Keep numbers, URLs, names, and factual claims intact.")
    return " ".join(notes)


def _sentence_instructions(
    sentence: Span,
    *,
    critique_items: list[RewriteCritiqueItem] | None,
    extra_instructions: list[str] | None,
) -> list[str] | None:
    notes: list[str] = []
    if critique_items:
        for item in critique_items:
            if item.span_start is None or item.span_end is None:
                continue
            if item.span_start < sentence.end_offset and item.span_end > sentence.start_offset:
                notes.append(item.message)
    if notes:
        return notes
    return extra_instructions


def _is_safe_rewrite(original: str, candidate: str) -> bool:
    return not post_check_rewrite(original, candidate)
