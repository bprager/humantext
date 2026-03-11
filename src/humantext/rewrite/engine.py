"""Strategy-driven rewrite helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass

from humantext.core.analysis import analyze_text
from humantext.core.segmentation import sentence_spans
from humantext.core.models import AnalysisResult, RewriteChange, RewriteCritiqueItem, RewriteResult
from humantext.llm.client import LLMClient, build_client
from humantext.llm.config import LLMConfig
from humantext.llm.tasks.critique_rewrite import critique_rewrite
from humantext.llm.tasks.rewrite_span import rewrite_flagged_spans
from humantext.rewrite.diff_explainer import build_change_log


@dataclass(frozen=True, slots=True)
class StrategyRule:
    strategy: str
    pattern: str
    replacement: str
    rationale: str


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
        r"(?m)^\s*(Additionally|Furthermore),\s*",
        "",
        "Dropped a stock transition at sentence start.",
    ),
    StrategyRule(
        "delete_redundant_summary",
        r"(?m)^\s*(Overall|In summary|In conclusion|To summarize),\s*",
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
                )
            )

    if not changes:
        for finding in analysis.findings:
            for strategy in finding.recommended_strategies:
                updated, strategy_changes = _apply_strategy(updated, strategy, finding.signal_code)
                changes.extend(strategy_changes)

    updated = _polish_sentences(updated)
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
                )
            )
        updated = _polish_sentences(updated)
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


def _apply_strategy(text: str, strategy: str, signal_code: str) -> tuple[str, list[RewriteChange]]:
    changes: list[RewriteChange] = []
    updated = text
    for rule in STRATEGY_RULES:
        if rule.strategy != strategy:
            continue
        new_text, count = re.subn(rule.pattern, rule.replacement, updated, flags=re.IGNORECASE | re.MULTILINE)
        if count:
            changes.append(
                RewriteChange(
                    signal_code=signal_code,
                    strategy=strategy,
                    before=updated,
                    after=new_text,
                    rationale=rule.rationale,
                )
            )
            updated = new_text
    return updated, changes



def _polish_sentences(text: str) -> str:
    if not text.strip():
        return text
    polished = text
    for span in reversed(sentence_spans(text)):
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
    available_strategies = {rule.strategy for rule in STRATEGY_RULES}
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
