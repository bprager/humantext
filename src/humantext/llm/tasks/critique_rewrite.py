"""Second-pass rewrite critique helpers."""

from __future__ import annotations

from humantext.core.analysis import analyze_text
from humantext.core.models import AnalysisResult, RewriteCritiqueItem
from humantext.llm.client import LLMClient
from humantext.llm.config import LLMConfig


def critique_rewrite(
    original_text: str,
    rewritten_text: str,
    *,
    mode: str,
    genre: str | None,
    profile_id: str | None,
    profile_summary: str | None,
    profile_traits: dict[str, str] | None,
    analysis_before: AnalysisResult,
    llm_config: LLMConfig | None,
    llm_client: LLMClient | None,
) -> tuple[list[RewriteCritiqueItem], list[str]]:
    """Run deterministic residual checks and optional LLM critique."""
    items: list[RewriteCritiqueItem] = []
    warnings: list[str] = []
    analysis_after = analyze_text(
        rewritten_text,
        mode=mode,
        genre=genre,
        profile_id=profile_id,
        profile_summary=profile_summary,
        profile_traits=profile_traits,
    )

    before_count = len(analysis_before.findings)
    after_count = len(analysis_after.findings)
    if after_count >= before_count and after_count > 0:
        items.append(
            RewriteCritiqueItem(
                source="deterministic",
                severity="medium",
                message=(
                    f"Rewrite did not reduce signal count ({before_count} before, {after_count} after). Review the revised spans."
                ),
            )
        )

    for finding in analysis_after.findings[:3]:
        items.append(
            RewriteCritiqueItem(
                source="deterministic",
                severity="low" if finding.effective_score < 0.7 else "medium",
                message=f"Residual signal: {finding.signal_code} on '{finding.span_text}'.",
                signal_code=finding.signal_code,
                span_start=finding.span_start,
                span_end=finding.span_end,
                span_text=finding.span_text,
            )
        )

    if llm_config and llm_config.supports("critique_rewrite"):
        client = llm_client
        if client is None:
            from humantext.llm.client import build_client

            client = build_client(llm_config)
        instructions = "Identify remaining generic language, meaning drift, and voice mismatch."
        try:
            critiques = client.critique_rewrite(
                original_text=original_text,
                rewritten_text=rewritten_text,
                instructions=instructions,
            )
        except Exception as exc:
            warnings.append(f"LLM critique failed: {exc}")
        else:
            for critique in critiques[:3]:
                items.append(
                    RewriteCritiqueItem(
                        source="llm",
                        severity="medium",
                        message=critique,
                    )
                )

    return items, warnings, analysis_after
