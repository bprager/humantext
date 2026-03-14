"""Rewrite Arena for counterfactual candidate generation."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

from humantext.core.analysis import analyze_text
from humantext.core.models import ArenaCandidate, ArenaResult, PlannedEdit, RewritePlan
from humantext.core.segmentation import Span, sentence_spans
from humantext.eval.metrics import edit_distance_ratio, negation_metrics, protected_token_metrics, qualifier_metrics
from humantext.llm.client import LLMClient
from humantext.llm.config import LLMConfig
from humantext.rewrite.diff_explainer import build_change_log
from humantext.rewrite.engine import _build_warnings, _normalize_whitespace, _polish_sentences, rewrite_text
from humantext.rewrite.planner import apply_plan, plan_deterministic_rewrite

_WORD_RE = re.compile(r"\b\w+\b")
_TRANSITIONS = ("however", "therefore", "additionally", "furthermore", "overall", "in summary")
_HEDGES = ("may", "might", "could", "perhaps", "suggests", "appears")
_ABSTRACT_NOUNS = ("landscape", "framework", "context", "significance", "interplay")
_CONTRACTIONS = re.compile(r"\b\w+'(?:t|re|ve|ll|d|s|m)\b", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class CandidateSpec:
    candidate_id: str
    label: str
    rationale: str


def review_rewrites(
    text: str,
    mode: str = "minimal",
    *,
    genre: str | None = None,
    profile_id: str | None = None,
    profile_summary: str | None = None,
    profile_traits: dict[str, str] | None = None,
    llm_config: LLMConfig | None = None,
    llm_client: LLMClient | None = None,
) -> ArenaResult:
    """Generate multiple rewrite candidates and recommend one."""
    analysis = analyze_text(
        text,
        mode=mode,
        genre=genre,
        profile_id=profile_id,
        profile_summary=profile_summary,
        profile_traits=profile_traits,
    )
    base_plan = plan_deterministic_rewrite(text, analysis.findings)
    specs = _candidate_specs(profile_traits, llm_config)
    candidates: list[ArenaCandidate] = []
    seen_outputs: set[str] = set()

    for spec in specs:
        if spec.candidate_id == "llm_challenger":
            candidate = _build_llm_candidate(
                text,
                spec,
                mode=mode,
                genre=genre,
                profile_id=profile_id,
                profile_summary=profile_summary,
                profile_traits=profile_traits,
                analysis=analysis,
                llm_config=llm_config,
                llm_client=llm_client,
            )
        else:
            candidate = _build_deterministic_candidate(
                text,
                spec,
                analysis=analysis,
                base_plan=base_plan,
                genre=genre,
                profile_id=profile_id,
                profile_summary=profile_summary,
                profile_traits=profile_traits,
            )
        if candidate is None:
            continue
        normalized_output = candidate.output_text.strip()
        if normalized_output in seen_outputs:
            continue
        seen_outputs.add(normalized_output)
        candidates.append(candidate)

    if not candidates:
        baseline_analysis = analyze_text(
            text,
            mode=mode,
            genre=genre,
            profile_id=profile_id,
            profile_summary=profile_summary,
            profile_traits=profile_traits,
        )
        candidates.append(
            ArenaCandidate(
                candidate_id="as_is",
                label="As Is",
                rationale="No distinct arena candidate improved on the original draft.",
                output_text=text,
                metrics=_candidate_metrics(text, analysis, text, baseline_analysis, [], profile_traits),
                changes=[],
                change_log=[],
                warnings=[],
            )
        )

    recommendation = max(candidates, key=lambda candidate: float(candidate.metrics.get("overall_score", 0.0)))
    return ArenaResult(
        summary=f"Compared {len(candidates)} rewrite arena candidate(s) for the current draft.",
        recommendation=recommendation.candidate_id,
        recommendation_rationale=_recommendation_rationale(recommendation),
        analysis=analysis,
        candidates=candidates,
    )


def _candidate_specs(
    profile_traits: dict[str, str] | None,
    llm_config: LLMConfig | None,
) -> list[CandidateSpec]:
    specs = [
        CandidateSpec("minimal", "Minimal Cut", "Touches the fewest spans while clearing the loudest signals."),
        CandidateSpec("balanced", "Balanced Draft", "Pushes harder on genericity while keeping the draft recognizably yours."),
        CandidateSpec("aggressive", "Hard Sweep", "Applies the full deterministic edit plan for maximum signal reduction."),
    ]
    if profile_traits:
        specs.append(
            CandidateSpec(
                "profile_match",
                "Profile Match",
                "Lets the learned voice profile veto lower-value edits that would flatten a legitimate style.",
            )
        )
    if llm_config and llm_config.supports("rewrite_spans"):
        specs.append(
            CandidateSpec(
                "llm_challenger",
                "LLM Challenger",
                "Brings in an optional model rewrite as a competing candidate under the same guardrails.",
            )
        )
    return specs


def _build_deterministic_candidate(
    text: str,
    spec: CandidateSpec,
    *,
    analysis: object,
    base_plan: RewritePlan,
    genre: str | None,
    profile_id: str | None,
    profile_summary: str | None,
    profile_traits: dict[str, str] | None,
) -> ArenaCandidate | None:
    selected = _select_lane_edits(text, base_plan.applied_edits, spec.candidate_id, profile_traits)
    if not selected and base_plan.applied_edits and spec.candidate_id != "profile_match":
        return None
    lane_plan = RewritePlan(
        planned_edits=list(base_plan.planned_edits),
        applied_edits=selected,
        rejected_edits=list(base_plan.rejected_edits),
    )
    output_text, changes = apply_plan(text, lane_plan)
    output_text = _polish_sentences(output_text, changes=changes)
    output_text = _normalize_whitespace(output_text)
    after_analysis = analyze_text(
        output_text,
        genre=genre,
        profile_id=profile_id,
        profile_summary=profile_summary,
        profile_traits=profile_traits,
    )
    warnings = [] if not changes else _build_warnings(analysis, changes)
    metrics = _candidate_metrics(text, analysis, output_text, after_analysis, changes, profile_traits)
    return ArenaCandidate(
        candidate_id=spec.candidate_id,
        label=spec.label,
        rationale=_candidate_rationale(spec, metrics),
        output_text=output_text,
        metrics=metrics,
        changes=changes,
        change_log=build_change_log(changes),
        warnings=warnings,
    )


def _build_llm_candidate(
    text: str,
    spec: CandidateSpec,
    *,
    mode: str,
    genre: str | None,
    profile_id: str | None,
    profile_summary: str | None,
    profile_traits: dict[str, str] | None,
    analysis: object,
    llm_config: LLMConfig | None,
    llm_client: LLMClient | None,
) -> ArenaCandidate | None:
    if llm_config is None:
        return None
    rewrite = rewrite_text(
        text,
        mode=mode,
        genre=genre,
        profile_id=profile_id,
        profile_summary=profile_summary,
        profile_traits=profile_traits,
        llm_config=llm_config,
        llm_client=llm_client,
    )
    after_analysis = analyze_text(
        rewrite.output_text,
        genre=genre,
        profile_id=profile_id,
        profile_summary=profile_summary,
        profile_traits=profile_traits,
    )
    metrics = _candidate_metrics(text, analysis, rewrite.output_text, after_analysis, rewrite.changes, profile_traits)
    return ArenaCandidate(
        candidate_id=spec.candidate_id,
        label=spec.label,
        rationale=_candidate_rationale(spec, metrics),
        output_text=rewrite.output_text,
        metrics=metrics,
        changes=list(rewrite.changes),
        change_log=list(rewrite.change_log),
        warnings=list(rewrite.warnings),
    )


def _select_lane_edits(
    text: str,
    edits: list[PlannedEdit],
    lane: str,
    profile_traits: dict[str, str] | None,
) -> list[PlannedEdit]:
    if lane == "aggressive":
        return list(edits)
    if not edits:
        return []

    ranked = sorted(edits, key=lambda edit: (-edit.effective_score, edit.start_offset, edit.end_offset))
    sentences = sentence_spans(text)
    sentence_counts: Counter[int] = Counter()
    selected: list[PlannedEdit] = []

    settings = {
        "minimal": (2, 1, 0.75),
        "balanced": (4, 2, 0.68),
        "profile_match": (3, 2, 0.7),
    }
    max_total, max_per_sentence, threshold = settings.get(lane, settings["balanced"])

    for edit in ranked:
        if edit.effective_score < threshold:
            continue
        if lane == "profile_match" and _profile_blocks_edit(edit, profile_traits):
            continue
        sentence_id = _sentence_id_for_edit(sentences, edit)
        if sentence_id is not None and sentence_counts[sentence_id] >= max_per_sentence:
            continue
        selected.append(edit)
        if sentence_id is not None:
            sentence_counts[sentence_id] += 1
        if len(selected) >= max_total:
            break

    if not selected and ranked and lane != "profile_match":
        selected.append(ranked[0])
    return sorted(selected, key=lambda edit: (edit.start_offset, edit.end_offset))


def _profile_blocks_edit(edit: PlannedEdit, profile_traits: dict[str, str] | None) -> bool:
    if not profile_traits:
        return False
    tolerance = str(profile_traits.get("tolerance_for_abstraction", "")).lower()
    directness = str(profile_traits.get("directness", "")).lower()
    transition_frequency = _safe_float(profile_traits.get("transition_frequency"))

    if edit.strategy in {"replace_with_concrete_fact", "delete_if_empty"} and tolerance == "high" and edit.effective_score < 0.82:
        return True
    if edit.strategy == "name_source_or_remove" and directness == "measured" and edit.effective_score < 0.84:
        return True
    if edit.strategy == "replace_canned_transition" and transition_frequency >= 0.12 and edit.effective_score < 0.82:
        return True
    return False


def _sentence_id_for_edit(sentences: list[Span], edit: PlannedEdit) -> int | None:
    for sentence in sentences:
        if sentence.start_offset <= edit.start_offset and sentence.end_offset >= edit.end_offset:
            return sentence.ordinal
    return None


def _candidate_metrics(
    original_text: str,
    before_analysis: object,
    rewritten_text: str,
    after_analysis: object,
    changes: list[object],
    profile_traits: dict[str, str] | None,
) -> dict[str, float | int]:
    before_signal_count = len(getattr(before_analysis, "findings"))
    after_signal_count = len(getattr(after_analysis, "findings"))
    signal_reduction_ratio = (
        round((before_signal_count - after_signal_count) / before_signal_count, 3)
        if before_signal_count
        else 1.0
    )
    protected_token_retention, _ = protected_token_metrics(original_text, rewritten_text)
    qualifier_retention, _ = qualifier_metrics(original_text, rewritten_text)
    negation_retention, _ = negation_metrics(original_text, rewritten_text)
    change_ratio = edit_distance_ratio(original_text, rewritten_text)
    voice_fit = _voice_fit_score(rewritten_text, profile_traits)
    preservation = round((protected_token_retention + qualifier_retention + negation_retention) / 3, 3)
    restraint = round(max(0.0, 1.0 - min(change_ratio / 0.4, 1.0)), 3)
    overall = round(0.4 * signal_reduction_ratio + 0.3 * preservation + 0.15 * voice_fit + 0.15 * restraint, 3)
    return {
        "before_signal_count": before_signal_count,
        "after_signal_count": after_signal_count,
        "signal_reduction_ratio": signal_reduction_ratio,
        "protected_token_retention": protected_token_retention,
        "qualifier_retention": qualifier_retention,
        "negation_retention": negation_retention,
        "edit_distance_ratio": change_ratio,
        "voice_fit": voice_fit,
        "overall_score": overall,
        "change_count": len(changes),
    }


def _candidate_rationale(spec: CandidateSpec, metrics: dict[str, float | int]) -> str:
    return (
        f"{spec.rationale} Reduced signals to {metrics['after_signal_count']} with "
        f"{metrics['change_count']} change(s) and score {metrics['overall_score']}."
    )


def _recommendation_rationale(candidate: ArenaCandidate) -> str:
    return (
        f"Recommended {candidate.label} because it reached overall score {candidate.metrics['overall_score']} "
        f"while leaving {candidate.metrics['after_signal_count']} signal(s)."
    )


def _voice_fit_score(text: str, profile_traits: dict[str, str] | None) -> float:
    if not profile_traits:
        return 0.5

    words = _WORD_RE.findall(text)
    sentences = [span.text for span in sentence_spans(text)]
    total_words = max(len(words), 1)
    sentence_lengths = [len(_WORD_RE.findall(sentence)) for sentence in sentences] or [0]
    avg_sentence = sum(sentence_lengths) / len(sentence_lengths)
    transition_rate = sum(text.lower().count(transition) for transition in _TRANSITIONS) / max(len(sentences), 1)
    hedge_rate = sum(text.lower().count(hedge) for hedge in _HEDGES) / total_words
    abstraction_rate = sum(text.lower().count(noun) for noun in _ABSTRACT_NOUNS) / total_words
    contraction_rate = len(_CONTRACTIONS.findall(text)) / total_words

    values: list[float] = []
    if "average_sentence_length" in profile_traits:
        values.append(_numeric_fit(avg_sentence, _safe_float(profile_traits.get("average_sentence_length")), tolerance=6.0))
    if "transition_frequency" in profile_traits:
        values.append(_numeric_fit(transition_rate, _safe_float(profile_traits.get("transition_frequency")), tolerance=0.08))
    if "hedging_frequency" in profile_traits:
        values.append(_numeric_fit(hedge_rate, _safe_float(profile_traits.get("hedging_frequency")), tolerance=0.03))
    if "contraction_usage" in profile_traits:
        values.append(_numeric_fit(contraction_rate, _safe_float(profile_traits.get("contraction_usage")), tolerance=0.03))
    if "formality" in profile_traits:
        values.append(_categorical_fit(_formality(avg_sentence, contraction_rate), str(profile_traits["formality"]).lower()))
    if "directness" in profile_traits:
        values.append(_categorical_fit(_directness(avg_sentence, hedge_rate), str(profile_traits["directness"]).lower()))
    if "tolerance_for_abstraction" in profile_traits:
        values.append(
            _categorical_fit(
                _abstraction_tolerance(abstraction_rate),
                str(profile_traits["tolerance_for_abstraction"]).lower(),
            )
        )
    if not values:
        return 0.5
    return round(sum(values) / len(values), 3)


def _numeric_fit(actual: float, target: float, *, tolerance: float) -> float:
    if tolerance <= 0:
        return 1.0
    delta = abs(actual - target)
    return round(max(0.0, 1.0 - min(delta / tolerance, 1.0)), 3)


def _categorical_fit(actual: str, expected: str) -> float:
    if actual == expected:
        return 1.0
    if {actual, expected} <= {"balanced", "direct", "measured"}:
        return 0.6
    if {actual, expected} <= {"low", "medium", "high"}:
        return 0.6
    return 0.2


def _formality(avg_sentence: float, contraction_rate: float) -> str:
    if avg_sentence >= 20 and contraction_rate < 0.01:
        return "high"
    if avg_sentence >= 14:
        return "medium"
    return "low"


def _directness(avg_sentence: float, hedge_rate: float) -> str:
    if avg_sentence <= 15 and hedge_rate < 0.01:
        return "direct"
    if hedge_rate > 0.02:
        return "measured"
    return "balanced"


def _abstraction_tolerance(rate: float) -> str:
    if rate >= 0.02:
        return "high"
    if rate >= 0.01:
        return "medium"
    return "low"


def _safe_float(value: object) -> float:
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
