"""Client abstractions for optional LLM support."""

from __future__ import annotations

from typing import Protocol

from humantext.llm.config import LLMConfig


class LLMClient(Protocol):
    def rewrite_span(self, *, sentence: str, instructions: str) -> str:
        """Rewrite one sentence span under caller-provided constraints."""

    def critique_rewrite(self, *, original_text: str, rewritten_text: str, instructions: str) -> list[str]:
        """Critique a full-document rewrite and return short findings."""


def build_client(config: LLMConfig) -> LLMClient:
    provider = config.provider.strip().lower()
    if provider in {"openai_compatible", "openai-compatible", "openai"}:
        from humantext.llm.adapters.openai_compatible import OpenAICompatibleClient

        return OpenAICompatibleClient(config)

    if provider == "ollama":
        from humantext.llm.adapters.openai_compatible import OpenAICompatibleClient

        return OpenAICompatibleClient(config)

    raise ValueError(f"Unsupported LLM provider: {config.provider}")
