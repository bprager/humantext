"""Evaluation runner for benchmark datasets."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field
from typing import Any

from humantext.core.analysis import analyze_text
from humantext.eval.dataset import EvalCase, load_dataset
from humantext.eval.metrics import (
    edit_distance_ratio,
    expected_token_metrics,
    negation_metrics,
    protected_token_metrics,
    qualifier_metrics,
)
from humantext.llm.config import LLMConfig
from humantext.rewrite.engine import rewrite_text


@dataclass(slots=True)
class EvalCaseResult:
    case_id: str
    task: str
    passed: bool
    failures: list[str]
    metrics: dict[str, Any]
    before_signal_codes: list[str] = field(default_factory=list)
    after_signal_codes: list[str] = field(default_factory=list)
    output_text: str | None = None
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class EvalRunResult:
    dataset_id: str
    dataset_version: str
    description: str
    aggregate_metrics: dict[str, Any]
    case_results: list[EvalCaseResult]

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "dataset_version": self.dataset_version,
            "description": self.description,
            "aggregate_metrics": self.aggregate_metrics,
            "case_results": [case_result.to_dict() for case_result in self.case_results],
        }


def run_evaluation(dataset_path: str, *, llm_config: LLMConfig | None = None) -> EvalRunResult:
    """Run the evaluation dataset and return structured results."""
    dataset = load_dataset(dataset_path)
    case_results = [
        _run_rewrite_case(case, llm_config=llm_config) if case.task == "rewrite" else _run_analyze_case(case)
        for case in dataset.cases
    ]
    return EvalRunResult(
        dataset_id=dataset.dataset_id,
        dataset_version=dataset.version,
        description=dataset.description,
        aggregate_metrics=_aggregate_metrics(case_results),
        case_results=case_results,
    )


def _run_analyze_case(case: EvalCase) -> EvalCaseResult:
    analysis = analyze_text(
        case.input_text,
        mode=case.mode,
        genre=case.genre,
        profile_summary=case.profile_summary,
        profile_traits=case.profile_traits,
    )
    signal_codes = [finding.signal_code for finding in analysis.findings]
    failures: list[str] = []
    expectations = case.expectations

    if expectations.max_findings is not None and len(signal_codes) > expectations.max_findings:
        failures.append(
            f"Detected {len(signal_codes)} finding(s), above allowed maximum of {expectations.max_findings}."
        )

    if expectations.allow_signal_codes:
        disallowed = sorted({code for code in signal_codes if code not in expectations.allow_signal_codes})
        if disallowed:
            failures.append(f"Detected unexpected signals: {', '.join(disallowed)}.")

    return EvalCaseResult(
        case_id=case.case_id,
        task=case.task,
        passed=not failures,
        failures=failures,
        metrics={"signal_count": len(signal_codes)},
        after_signal_codes=signal_codes,
    )


def _run_rewrite_case(case: EvalCase, *, llm_config: LLMConfig | None) -> EvalCaseResult:
    analysis_before = analyze_text(
        case.input_text,
        mode=case.mode,
        genre=case.genre,
        profile_summary=case.profile_summary,
        profile_traits=case.profile_traits,
    )
    rewrite = rewrite_text(
        case.input_text,
        mode=case.mode,
        genre=case.genre,
        profile_summary=case.profile_summary,
        profile_traits=case.profile_traits,
        llm_config=llm_config,
    )
    analysis_after = analyze_text(
        rewrite.output_text,
        mode=case.mode,
        genre=case.genre,
        profile_summary=case.profile_summary,
        profile_traits=case.profile_traits,
    )
    before_signal_codes = [finding.signal_code for finding in analysis_before.findings]
    after_signal_codes = [finding.signal_code for finding in analysis_after.findings]
    before_counts = Counter(before_signal_codes)
    after_counts = Counter(after_signal_codes)
    failures: list[str] = []
    expectations = case.expectations

    for signal_code in expectations.must_reduce_signal_codes:
        if before_counts[signal_code] == 0:
            failures.append(f"Expected source signal {signal_code} was not present before rewrite.")
            continue
        if after_counts[signal_code] >= before_counts[signal_code]:
            failures.append(
                f"Rewrite did not reduce {signal_code} ({before_counts[signal_code]} before, {after_counts[signal_code]} after)."
            )

    expected_token_retention, missing_expected_tokens = expected_token_metrics(
        expectations.preserve_tokens,
        rewrite.output_text,
    )
    if missing_expected_tokens:
        failures.append(f"Rewrite dropped expected tokens: {', '.join(missing_expected_tokens)}.")

    protected_token_retention, missing_protected_tokens = protected_token_metrics(case.input_text, rewrite.output_text)
    qualifier_retention, missing_qualifiers = qualifier_metrics(case.input_text, rewrite.output_text)
    negation_retention, missing_negations = negation_metrics(case.input_text, rewrite.output_text)
    change_ratio = edit_distance_ratio(case.input_text, rewrite.output_text)
    signal_reduction_ratio = (
        round((len(before_signal_codes) - len(after_signal_codes)) / len(before_signal_codes), 3)
        if before_signal_codes
        else 0.0
    )

    if missing_protected_tokens:
        failures.append(f"Rewrite dropped protected tokens: {', '.join(missing_protected_tokens)}.")
    if expectations.preserve_qualifiers and missing_qualifiers:
        failures.append(f"Rewrite dropped qualifiers: {', '.join(missing_qualifiers)}.")
    if expectations.preserve_negations and missing_negations:
        failures.append(f"Rewrite dropped negations: {', '.join(missing_negations)}.")
    if expectations.max_edit_distance_ratio is not None and change_ratio > expectations.max_edit_distance_ratio:
        failures.append(
            f"Rewrite edit distance ratio {change_ratio} exceeded max {expectations.max_edit_distance_ratio}."
        )

    metrics = {
        "before_signal_count": len(before_signal_codes),
        "after_signal_count": len(after_signal_codes),
        "signal_reduction_ratio": signal_reduction_ratio,
        "expected_token_retention": expected_token_retention,
        "protected_token_retention": protected_token_retention,
        "qualifier_retention": qualifier_retention,
        "negation_retention": negation_retention,
        "edit_distance_ratio": change_ratio,
        "change_count": len(rewrite.changes),
    }

    return EvalCaseResult(
        case_id=case.case_id,
        task=case.task,
        passed=not failures,
        failures=failures,
        metrics=metrics,
        before_signal_codes=before_signal_codes,
        after_signal_codes=after_signal_codes,
        output_text=rewrite.output_text,
        warnings=list(rewrite.warnings),
    )


def _aggregate_metrics(case_results: list[EvalCaseResult]) -> dict[str, Any]:
    rewrite_results = [result for result in case_results if result.task == "rewrite"]
    analyze_results = [result for result in case_results if result.task == "analyze"]
    passed_cases = sum(1 for result in case_results if result.passed)

    return {
        "total_cases": len(case_results),
        "passed_cases": passed_cases,
        "pass_rate": _ratio(passed_cases, len(case_results)),
        "rewrite_case_pass_rate": _ratio(sum(1 for result in rewrite_results if result.passed), len(rewrite_results)),
        "analyze_case_pass_rate": _ratio(sum(1 for result in analyze_results if result.passed), len(analyze_results)),
        "mean_signal_reduction_ratio": _mean_metric(rewrite_results, "signal_reduction_ratio"),
        "protected_token_retention_rate": _mean_metric(rewrite_results, "protected_token_retention"),
        "qualifier_retention_rate": _mean_metric(rewrite_results, "qualifier_retention"),
        "negation_retention_rate": _mean_metric(rewrite_results, "negation_retention"),
        "mean_edit_distance_ratio": _mean_metric(rewrite_results, "edit_distance_ratio"),
        "mean_findings_on_analyze_cases": _mean_metric(analyze_results, "signal_count"),
    }


def _mean_metric(case_results: list[EvalCaseResult], metric_name: str) -> float:
    values = [float(result.metrics[metric_name]) for result in case_results if metric_name in result.metrics]
    if not values:
        return 0.0
    return round(sum(values) / len(values), 3)


def _ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 3)
