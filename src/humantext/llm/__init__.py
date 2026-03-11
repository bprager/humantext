"""Optional LLM integration layer."""

from humantext.llm.client import build_client
from humantext.llm.config import LLMConfig

__all__ = ["LLMConfig", "build_client"]
