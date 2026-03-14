"""Offset-aware deterministic rewrite planning."""

from __future__ import annotations

import re

from humantext.core.models import Finding, PlannedEdit, RewriteChange, RewritePlan
from humantext.core.segmentation import Span, sentence_spans


class StrategyRule:
    __slots__ = ("strategy", "pattern", "replacement", "rationale")

    def __init__(self, strategy: str, pattern: str, replacement: str, rationale: str) -> None:
        self.strategy = strategy
        self.pattern = pattern
        self.replacement = replacement
        self.rationale = rationale


STRATEGY_RULES: tuple[StrategyRule, ...] = (
    StrategyRule(
        "remove_teacherly_preface",
        r"\bIt is important to note that\s*",
        "",
        "Removed teacherly framing so the sentence states the point directly.",
    ),
    StrategyRule("remove_teacherly_preface", r"\bWorth noting,?\s*", "", "Removed teacherly preface."),
    StrategyRule(
        "replace_canned_transition",
        r"^\s*(Additionally|Furthermore),\s*",
        "",
        "Dropped a stock transition at sentence start.",
    ),
    StrategyRule(
        "delete_redundant_summary",
        r"^\s*(Overall|In summary|In conclusion|To summarize),\s*",
        "",
        "Removed summary framing that usually repeats the paragraph.",
    ),
    StrategyRule("simplify_to_plain_statement", r"\bserves as\b", "is", "Simplified inflated copula phrasing."),
    StrategyRule("simplify_to_plain_statement", r"\bstands as\b", "is", "Simplified inflated copula phrasing."),
    StrategyRule("simplify_to_plain_statement", r"\bfeatures\b", "has", "Simplified inflated copula phrasing."),
    StrategyRule("simplify_to_plain_statement", r"\boffers\b", "has", "Simplified inflated copula phrasing."),
    StrategyRule("neutralize_promotional_language", r"\bvibrant\b", "active", "Neutralized promotional language."),
    StrategyRule("neutralize_promotional_language", r"\brenowned\b", "well-known", "Neutralized promotional language."),
    StrategyRule("neutralize_promotional_language", r"\bgroundbreaking\b", "notable", "Neutralized promotional language."),
    StrategyRule("neutralize_promotional_language", r"\bremarkable\b", "notable", "Neutralized ungrounded praise."),
    StrategyRule("remove_chat_residue", r"\bI hope this helps\.?\s*", "", "Removed conversational assistant residue."),
    StrategyRule("remove_chat_residue", r"\bWould you like[^.?!]*[.?!]\s*", "", "Removed assistant-style prompt residue."),
    StrategyRule(
        "remove_chat_residue",
        r"\bAs of my last training update[^.?!]*[.?!]\s*",
        "",
        "Removed model-era disclaimer language.",
    ),
    StrategyRule(
        "remove_chat_residue",
        r"\bAs an AI language model[^.?!]*[.?!]\s*",
        "",
        "Removed explicit model disclosure residue.",
    ),
    StrategyRule("swap_abstract_nouns_for_verbs", r"\bin order to\b", "to", "Shortened verbose abstraction."),
    StrategyRule(
        "state_known_limits_plainly",
        r"\bthere appears to be little information\b",
        "little verified information is available",
        "Stated the sourcing limit directly.",
    ),
    StrategyRule("replace_with_concrete_fact", r"\ba pivotal moment\b", "a concrete change", "Reduced inflated significance language."),
    StrategyRule("replace_with_concrete_fact", r"\bpivotal moment\b", "concrete change", "Reduced inflated significance language."),
    StrategyRule("replace_with_concrete_fact", r"\ba crucial role\b", "an important role", "Reduced inflated significance language."),
    StrategyRule("replace_with_concrete_fact", r"\bcrucial role\b", "important role", "Reduced inflated significance language."),
    StrategyRule("replace_with_concrete_fact", r"\bmarks? a shift\b", "marks a concrete change", "Reduced inflated significance language."),
    StrategyRule("delete_if_empty", r"\breflects broader trends\b", "reflects documented changes", "Removed empty context padding."),
    StrategyRule("delete_if_empty", r"\bcontributes to the wider landscape\b", "adds to the record", "Removed empty context padding."),
    StrategyRule("delete_if_empty", r"\bbroader landscape\b", "documented context", "Removed empty context padding."),
    StrategyRule("delete_if_empty", r"\bfuture prospects\b", "next steps", "Reduced canned future framing."),
    StrategyRule("delete_if_empty", r"\bfuture outlook\b", "next steps", "Reduced canned future framing."),
    StrategyRule("name_source_or_remove", r"\b[Ee]xperts argue that\s*", "", "Removed vague attribution that named no source."),
    StrategyRule("name_source_or_remove", r"\b[Ee]xperts argue\s*", "", "Removed vague attribution that named no source."),
    StrategyRule("name_source_or_remove", r"\b[Oo]bservers say that\s*", "", "Removed vague attribution that named no source."),
    StrategyRule("name_source_or_remove", r"\b[Oo]bservers say\s*", "", "Removed vague attribution that named no source."),
    StrategyRule("name_source_or_remove", r"\b[Ii]ndustry reports suggest that\s*", "", "Removed vague attribution that named no source."),
    StrategyRule("name_source_or_remove", r"\b[Ii]ndustry reports suggest\s*", "", "Removed vague attribution that named no source."),
)


def supported_strategies() -> set[str]:
    return {rule.strategy for rule in STRATEGY_RULES}


def plan_deterministic_rewrite(text: str, findings: list[Finding]) -> RewritePlan:
    planned: list[PlannedEdit] = []
    sentences = sentence_spans(text)
    for finding in findings:
        sentence = _sentence_for_finding(sentences, finding)
        if sentence is None:
            continue
        for strategy in finding.recommended_strategies:
            planned.extend(_plan_strategy(text, sentence, finding, strategy))
    applied, rejected = _resolve_conflicts(planned)
    return RewritePlan(planned_edits=planned, applied_edits=applied, rejected_edits=rejected)


def apply_plan(text: str, plan: RewritePlan) -> tuple[str, list[RewriteChange]]:
    if not plan.applied_edits:
        return text, []

    pieces: list[str] = []
    changes: list[RewriteChange] = []
    cursor = 0
    final_offset = 0
    for edit in sorted(plan.applied_edits, key=lambda item: (item.start_offset, item.end_offset)):
        untouched = text[cursor:edit.start_offset]
        pieces.append(untouched)
        final_offset += len(untouched)
        span_start = final_offset
        pieces.append(edit.after)
        final_offset += len(edit.after)
        span_end = final_offset
        cursor = edit.end_offset
        changes.append(
            RewriteChange(
                signal_code=edit.signal_code,
                strategy=edit.strategy,
                before=edit.before,
                after=edit.after,
                rationale=edit.rationale,
                span_start=span_start,
                span_end=span_end,
                scope=edit.scope,
            )
        )
    pieces.append(text[cursor:])
    return "".join(pieces), changes


def _plan_strategy(text: str, sentence: Span, finding: Finding, strategy: str) -> list[PlannedEdit]:
    sentence_text = text[sentence.start_offset:sentence.end_offset]
    edits: list[PlannedEdit] = []
    for rule in STRATEGY_RULES:
        if rule.strategy != strategy:
            continue
        for match in re.finditer(rule.pattern, sentence_text, re.IGNORECASE | re.MULTILINE):
            start_offset = sentence.start_offset + match.start()
            end_offset = sentence.start_offset + match.end()
            if not _overlaps_span(start_offset, end_offset, finding.span_start, finding.span_end):
                continue
            before = text[start_offset:end_offset]
            after = re.sub(rule.pattern, rule.replacement, before, count=1, flags=re.IGNORECASE | re.MULTILINE)
            if before == after:
                continue
            edits.append(
                PlannedEdit(
                    signal_code=finding.signal_code,
                    strategy=strategy,
                    start_offset=start_offset,
                    end_offset=end_offset,
                    before=before,
                    after=after,
                    rationale=rule.rationale,
                    effective_score=finding.effective_score,
                    scope="finding" if (start_offset, end_offset) == (finding.span_start, finding.span_end) else "sentence",
                )
            )
            break
    return edits


def _resolve_conflicts(planned: list[PlannedEdit]) -> tuple[list[PlannedEdit], list[PlannedEdit]]:
    applied: list[PlannedEdit] = []
    rejected: list[PlannedEdit] = []
    seen: set[tuple[int, int, str, str]] = set()

    ordered = [edit for _, edit in sorted(enumerate(planned), key=lambda item: (-item[1].effective_score, item[0]))]
    for edit in ordered:
        duplicate_key = (edit.start_offset, edit.end_offset, edit.after, edit.strategy)
        if duplicate_key in seen:
            edit.status = "rejected"
            edit.rejection_reason = "duplicate"
            rejected.append(edit)
            continue
        conflict = next((item for item in applied if _overlaps_edit(item, edit)), None)
        if conflict is not None:
            edit.status = "rejected"
            edit.rejection_reason = f"overlaps:{conflict.strategy}"
            rejected.append(edit)
            continue
        edit.status = "applied"
        applied.append(edit)
        seen.add(duplicate_key)

    applied.sort(key=lambda item: (item.start_offset, item.end_offset))
    rejected.sort(key=lambda item: (item.start_offset, item.end_offset, item.strategy))
    return applied, rejected


def _sentence_for_finding(sentences: list[Span], finding: Finding) -> Span | None:
    for sentence in sentences:
        if sentence.start_offset <= finding.span_start and sentence.end_offset >= finding.span_end:
            return sentence
    return None


def _overlaps_edit(left: PlannedEdit, right: PlannedEdit) -> bool:
    return _overlaps_span(left.start_offset, left.end_offset, right.start_offset, right.end_offset)


def _overlaps_span(left_start: int, left_end: int, right_start: int, right_end: int) -> bool:
    return left_start < right_end and right_start < left_end
