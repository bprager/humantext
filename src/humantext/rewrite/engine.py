"""Strategy-driven rewrite helpers."""

from __future__ import annotations

import re

from humantext.core.analysis import analyze_text
from humantext.core.segmentation import Span, sentence_spans
from humantext.core.models import AnalysisResult, RewriteChange, RewriteCritiqueItem, RewriteResult
from humantext.llm.client import LLMClient, build_client
from humantext.llm.config import LLMConfig
from humantext.llm.tasks.critique_rewrite import critique_rewrite
from humantext.llm.tasks.rewrite_span import rewrite_flagged_spans
from humantext.rewrite.diff_explainer import build_change_log
from humantext.rewrite.planner import apply_plan, plan_deterministic_rewrite, supported_strategies


def rewrite_text(
    text: str,
    mode: str = "minimal",
    *,
    genre: str | None = None,
    profile_id: str | None = None,
    profile_summary: str | None = None,
    profile_traits: dict[str, str] | None = None,
    llm_config: LLMConfig | None = None,
    llm_client: LLMClient | None = None,
) -> RewriteResult:
    """Rewrite text using the strategies recommended by the analysis layer."""
    client: LLMClient | None = None
    analysis = analyze_text(
        text,
        mode=mode,
        genre=genre,
        profile_id=profile_id,
        profile_summary=profile_summary,
        profile_traits=profile_traits,
    )
    updated = text
    changes: list[RewriteChange] = []
    llm_warnings: list[str] = []

    if llm_config and llm_config.supports("rewrite_spans"):
        client = llm_client or build_client(llm_config)
        updated, llm_changes, llm_warnings = rewrite_flagged_spans(
            text,
            analysis.findings,
            mode=mode,
            profile_summary=profile_summary,
            config=llm_config,
            client=client,
        )
        for change in llm_changes:
            changes.append(
                RewriteChange(
                    signal_code=change["signal_codes"],
                    strategy="llm_rewrite_span",
                    before=change["before"],
                    after=change["after"],
                    rationale=change["rationale"],
                    scope="sentence",
                )
            )

    if not changes:
        plan = plan_deterministic_rewrite(text, analysis.findings)
        updated, changes = apply_plan(text, plan)

    updated = _polish_sentences(updated, changes=changes)
    updated = _normalize_whitespace(updated)
    warnings = llm_warnings + _build_warnings(analysis, changes)
    critique, critique_warnings, analysis_after = critique_rewrite(
        text,
        updated,
        mode=mode,
        genre=genre,
        profile_id=profile_id,
        profile_summary=profile_summary,
        profile_traits=profile_traits,
        analysis_before=analysis,
        llm_config=llm_config,
        llm_client=client or llm_client,
    )
    warnings.extend(critique_warnings)
    if llm_config and llm_config.supports("second_pass_rewrite") and analysis_after.findings:
        client = client or llm_client or build_client(llm_config)
        targeted_keys = {
            (item.signal_code, item.span_start, item.span_end)
            for item in critique
            if item.signal_code is not None and item.span_start is not None and item.span_end is not None
        }
        targeted_findings = [
            finding
            for finding in analysis_after.findings
            if (finding.signal_code, finding.span_start, finding.span_end) in targeted_keys
        ]
        if targeted_findings:
            updated, second_pass_changes, second_pass_warnings = rewrite_flagged_spans(
                updated,
                targeted_findings,
                mode=mode,
                profile_summary=profile_summary,
                config=llm_config,
                client=client,
                critique_items=critique,
            )
        else:
            second_pass_changes = []
            second_pass_warnings = []
        warnings.extend(second_pass_warnings)
        for change in second_pass_changes:
            changes.append(
                RewriteChange(
                    signal_code=change["signal_codes"],
                    strategy="llm_rewrite_second_pass",
                    before=change["before"],
                    after=change["after"],
                    rationale="Applied second-pass LLM rewrite using critique feedback.",
                    scope="sentence",
                )
            )
        updated = _polish_sentences(updated, changes=changes)
        updated = _normalize_whitespace(updated)
        critique, critique_warnings, _ = critique_rewrite(
            text,
            updated,
            mode=mode,
            genre=genre,
            profile_id=profile_id,
            profile_summary=profile_summary,
            profile_traits=profile_traits,
            analysis_before=analysis,
            llm_config=llm_config,
            llm_client=client,
        )
        warnings.extend(critique_warnings)
    if any("Rejected unsafe LLM rewrite" in warning for warning in warnings):
        critique.append(
            RewriteCritiqueItem(
                source="deterministic",
                severity="medium",
                message="An unsafe LLM rewrite was rejected and the deterministic fallback path was used.",
            )
        )
    change_log = build_change_log(changes)
    return RewriteResult(
        output_text=updated,
        changes=changes,
        warnings=warnings,
        analysis=analysis,
        change_log=change_log,
        critique=critique,
    )


def _polish_sentences(text: str, *, changes: list[RewriteChange] | None = None) -> str:
    if not text.strip():
        return text
    spans = _touched_sentences(text, changes) if changes else sentence_spans(text)
    if not spans:
        spans = sentence_spans(text)
    polished = text
    for span in reversed(spans):
        sentence = polished[span.start_offset:span.end_offset]
        cleaned = _clean_sentence(sentence)
        polished = polished[:span.start_offset] + cleaned + polished[span.end_offset:]
    return polished


def _clean_sentence(sentence: str) -> str:
    sentence = sentence.strip()
    sentence = re.sub(r"^(and|but)\s+", "", sentence, flags=re.IGNORECASE)
    sentence = re.sub(r"\bthis reflects documented changes\b", "This describes documented changes", sentence, flags=re.IGNORECASE)
    sentence = re.sub(r"\bthis is a concrete change\b", "This describes a concrete change", sentence, flags=re.IGNORECASE)
    sentence = re.sub(r"\bthis is concrete change\b", "This describes a concrete change", sentence, flags=re.IGNORECASE)
    if sentence and sentence[0].islower():
        sentence = sentence[0].upper() + sentence[1:]
    return sentence


def _normalize_whitespace(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"\s+([.,;:!?])", r"\1", text)
    text = re.sub(r"\b(is|are|was|were) a\s+\.", r"\1.", text)
    text = re.sub(r"\s+\.", ".", text)
    text = text.strip()
    if text and text[0].islower():
        text = text[0].upper() + text[1:]
    return text


def _build_warnings(analysis: AnalysisResult, changes: list[RewriteChange]) -> list[str]:
    available_strategies = supported_strategies()
    unresolved = [
        finding.signal_code
        for finding in analysis.findings
        if not any(strategy in available_strategies for strategy in finding.recommended_strategies)
        and not any(change.strategy == "llm_rewrite_span" for change in changes)
    ]
    if analysis.findings and not changes:
        return ["Signals were detected, but no automatic strategy rule was available for them yet."]
    if unresolved:
        return [f"Automatic rewrite rules are not implemented yet for: {', '.join(sorted(set(unresolved)))}."]
    if len(changes) > 8:
        return ["Rewrite touched many spans; review for tone drift."]
    return []


def _touched_sentences(text: str, changes: list[RewriteChange] | None) -> list[Span]:
    if not changes:
        return []
    touched: list[Span] = []
    for span in sentence_spans(text):
        if any(_change_touches_sentence(change, span) for change in changes):
            touched.append(span)
    return touched


def _change_touches_sentence(change: RewriteChange, sentence: Span) -> bool:
    if change.span_start is None or change.span_end is None:
        return False
    if change.span_start == change.span_end:
        return sentence.start_offset <= change.span_start <= sentence.end_offset
    return change.span_start < sentence.end_offset and change.span_end > sentence.start_offset
