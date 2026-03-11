"""Configuration helpers for optional LLM augmentation."""

from __future__ import annotations

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Mapping


DEFAULT_CAPABILITIES = ("rewrite_spans", "critique_rewrite", "second_pass_rewrite")
DEFAULT_DOTENV_PATH = ".env"


def load_dotenv(path: str | Path | None = None) -> dict[str, str]:
    """Load a simple KEY=VALUE dotenv file without mutating process env."""
    env_path = Path(path or DEFAULT_DOTENV_PATH)
    if not env_path.is_file():
        return {}

    values: dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key] = value
    return values


def get_runtime_env(path: str | Path | None = None) -> dict[str, str]:
    """Merge `.env` defaults with the real environment, favoring real env values."""
    merged = load_dotenv(path)
    merged.update(os.environ)
    return merged


def _coalesce_text(*values: object | None) -> str:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def _coalesce_value(*values: Any) -> Any:
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        return value
    return None


def _coerce_capabilities(raw: Any) -> tuple[str, ...]:
    if isinstance(raw, str):
        return tuple(item.strip() for item in raw.split(",") if item.strip()) or DEFAULT_CAPABILITIES
    if isinstance(raw, (list, tuple)):
        return tuple(str(item).strip() for item in raw if str(item).strip()) or DEFAULT_CAPABILITIES
    return DEFAULT_CAPABILITIES


def _coerce_int(raw: Any, default: int) -> int:
    try:
        return max(1, int(raw))
    except (TypeError, ValueError):
        return default


def _coerce_float(raw: Any, default: float) -> float:
    try:
        return float(raw)
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True, slots=True)
class LLMConfig:
    provider: str
    base_url: str
    model: str
    api_key_env: str = "HUMANTEXT_LLM_API_KEY"
    timeout_seconds: int = 30
    temperature: float = 0.2
    enabled_capabilities: tuple[str, ...] = field(
        default_factory=lambda: DEFAULT_CAPABILITIES
    )
    environment: Mapping[str, str] = field(default_factory=dict, repr=False, compare=False)

    @property
    def api_key(self) -> str | None:
        return self.environment.get(self.api_key_env)

    def supports(self, capability: str) -> bool:
        return capability in self.enabled_capabilities

    @classmethod
    def from_mapping(cls, payload: dict[str, Any] | None) -> "LLMConfig | None":
        payload = payload or {}
        runtime_env = get_runtime_env()
        provider = _coalesce_text(payload.get("provider"), runtime_env.get("HUMANTEXT_LLM_PROVIDER"))
        base_url = _coalesce_text(payload.get("base_url"), runtime_env.get("HUMANTEXT_LLM_BASE_URL"))
        model = _coalesce_text(payload.get("model"), runtime_env.get("HUMANTEXT_LLM_MODEL"))
        if not provider or not base_url or not model:
            return None

        enabled_capabilities = _coerce_capabilities(
            _coalesce_value(payload.get("enabled_capabilities"), runtime_env.get("HUMANTEXT_LLM_CAPABILITIES"))
        )

        return cls(
            provider=provider,
            base_url=base_url,
            model=model,
            api_key_env=_coalesce_text(
                payload.get("api_key_env"),
                runtime_env.get("HUMANTEXT_LLM_API_KEY_ENV"),
                "HUMANTEXT_LLM_API_KEY",
            ),
            timeout_seconds=_coerce_int(
                _coalesce_value(payload.get("timeout_seconds"), runtime_env.get("HUMANTEXT_LLM_TIMEOUT")),
                30,
            ),
            temperature=_coerce_float(
                _coalesce_value(payload.get("temperature"), runtime_env.get("HUMANTEXT_LLM_TEMPERATURE")),
                0.2,
            ),
            enabled_capabilities=enabled_capabilities,
            environment=runtime_env,
        )
