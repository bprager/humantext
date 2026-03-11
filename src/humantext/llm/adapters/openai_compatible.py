"""OpenAI-compatible HTTP adapter."""

from __future__ import annotations

import json
from dataclasses import dataclass
from urllib import request

from humantext.llm.config import LLMConfig


@dataclass(slots=True)
class OpenAICompatibleClient:
    config: LLMConfig

    def rewrite_span(self, *, sentence: str, instructions: str) -> str:
        prompt = (
            "Rewrite the sentence so it reads more naturally and specifically while preserving meaning. "
            "Return only the rewritten sentence. No bullets, no JSON, no explanation.\n\n"
            f"{instructions}\n\n"
            f"Original sentence:\n{sentence}"
        )
        payload = {
            "model": self.config.model,
            "temperature": self.config.temperature,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an editorial rewrite engine. Preserve facts, qualifiers, named entities, numbers, "
                        "and domain terms unless explicitly instructed otherwise."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        }
        response = self._post_json("/chat/completions", payload)
        choices = response.get("choices", [])
        if not choices:
            raise ValueError("LLM response contained no choices")
        message = choices[0].get("message", {})
        content = message.get("content", "")
        if isinstance(content, list):
            content = "".join(part.get("text", "") for part in content if isinstance(part, dict))
        cleaned = _clean_response_text(str(content))
        if not cleaned:
            raise ValueError("LLM returned an empty rewrite")
        return cleaned

    def critique_rewrite(self, *, original_text: str, rewritten_text: str, instructions: str) -> list[str]:
        prompt = (
            "Review the rewritten text against the original and identify up to three concise editorial concerns. "
            "Focus on meaning drift, remaining generic language, or tone mismatch. "
            "Return JSON only with a 'critiques' array of strings.\n\n"
            f"{instructions}\n\n"
            f"Original text:\n{original_text}\n\n"
            f"Rewritten text:\n{rewritten_text}"
        )
        payload = {
            "model": self.config.model,
            "temperature": self.config.temperature,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an editorial reviewer. Return strict JSON only. Do not invent unsupported claims."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        }
        response = self._post_json("/chat/completions", payload)
        choices = response.get("choices", [])
        if not choices:
            raise ValueError("LLM response contained no choices")
        message = choices[0].get("message", {})
        content = message.get("content", "")
        if isinstance(content, list):
            content = "".join(part.get("text", "") for part in content if isinstance(part, dict))
        raw = _clean_response_text(str(content))
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"LLM critique did not return JSON: {exc}") from exc
        critiques = payload.get("critiques", [])
        if not isinstance(critiques, list):
            raise ValueError("LLM critique payload is missing a critiques array")
        return [str(item).strip() for item in critiques if str(item).strip()]

    def _post_json(self, path: str, payload: dict[str, object]) -> dict[str, object]:
        endpoint = self.config.base_url.rstrip("/") + path
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        raw_request = request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with request.urlopen(raw_request, timeout=self.config.timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))


def _clean_response_text(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
        if "\n" in cleaned:
            cleaned = cleaned.split("\n", 1)[1].strip()
    cleaned = cleaned.strip().strip('"').strip("'")
    return " ".join(cleaned.split())
