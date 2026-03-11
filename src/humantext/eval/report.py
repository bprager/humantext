"""Formatting helpers for evaluation reports."""

from __future__ import annotations

from humantext.eval.runner import EvalRunResult


def render_markdown_report(result: EvalRunResult) -> str:
    """Render an evaluation run as a short markdown report."""
    lines = [
        "# HumanText Evaluation Report",
        "",
        f"- Dataset: `{result.dataset_id}`",
        f"- Version: `{result.dataset_version}`",
        f"- Description: {result.description or 'n/a'}",
        "",
        "## Aggregate Metrics",
        "",
    ]
    for key, value in result.aggregate_metrics.items():
        lines.append(f"- `{key}`: `{value}`")

    lines.extend(
        [
            "",
            "## Case Results",
            "",
            "| Case | Task | Passed | Signals | Edit Distance | Failures |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for case_result in result.case_results:
        signal_summary = _signal_summary(case_result)
        edit_distance = case_result.metrics.get("edit_distance_ratio", "n/a")
        failures = "; ".join(case_result.failures) if case_result.failures else "none"
        failures = failures.replace("|", "\\|")
        lines.append(
            f"| `{case_result.case_id}` | `{case_result.task}` | `{str(case_result.passed).lower()}` | "
            f"`{signal_summary}` | `{edit_distance}` | {failures} |"
        )
    return "\n".join(lines)


def _signal_summary(case_result: object) -> str:
    before = getattr(case_result, "before_signal_codes", [])
    after = getattr(case_result, "after_signal_codes", [])
    if before:
        return f"{len(before)} -> {len(after)}"
    return str(len(after))
