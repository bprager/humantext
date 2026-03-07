"""Edit-planning helpers built on top of analysis and rewrite passes."""

from __future__ import annotations

from humantext.core.analysis import analyze_text
from humantext.core.models import EditPriority, EditSuggestion
from humantext.rewrite.engine import rewrite_text

RISK_NOTES = {
    "replace_with_concrete_fact": "Verify the replacement still names the right concrete fact.",
    "replace_with_specific_claim": "Check whether a specific claim can be supported with evidence.",
    "name_source_or_remove": "Remove only if the surrounding claim still stands without attribution.",
    "delete_if_empty": "Low risk if the phrase adds no substantive content.",
    "delete_redundant_summary": "Low risk if the previous paragraph already carries the point.",
    "simplify_to_plain_statement": "Review tone if the original phrasing carried legal or scientific nuance.",
}


def suggest_edits(
    text: str,
    mode: str = "minimal",
    *,
    genre: str | None = None,
    profile_id: str | None = None,
    profile_summary: str | None = None,
    profile_traits: dict[str, str] | None = None,
) -> EditSuggestion:
    """Return a ranked edit plan with sample rewrites."""
    analysis = analyze_text(
        text,
        mode=mode,
        genre=genre,
        profile_id=profile_id,
        profile_summary=profile_summary,
        profile_traits=profile_traits,
    )
    priorities: list[EditPriority] = []
    for finding in analysis.findings:
        strategy = finding.recommended_strategies[0] if finding.recommended_strategies else "review"
        scope = "sentence" if len(finding.span_text.split()) <= 12 else "paragraph"
        priorities.append(
            EditPriority(
                signal_code=finding.signal_code,
                goal=finding.description,
                strategy_code=strategy,
                edit_scope=scope,
                risk_note=RISK_NOTES.get(strategy, "Review manually if domain-specific nuance matters."),
                span_text=finding.span_text,
                effective_score=finding.effective_score,
            )
        )

    rewrite = rewrite_text(
        text,
        mode=mode,
        genre=genre,
        profile_id=profile_id,
        profile_summary=profile_summary,
        profile_traits=profile_traits,
    )
    sample_edits = []
    for change in rewrite.changes[:5]:
        sample_edits.append(
            {
                "signal_code": change.signal_code,
                "strategy_code": change.strategy,
                "before": _clip(change.before),
                "after": _clip(change.after),
            }
        )

    return EditSuggestion(edit_plan=priorities, sample_edits=sample_edits, analysis=analysis)


def _clip(text: str, limit: int = 160) -> str:
    text = " ".join(text.strip().split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."
