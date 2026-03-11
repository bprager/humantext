"""Evaluation dataset loading helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class EvalExpectations:
    max_findings: int | None = None
    allow_signal_codes: tuple[str, ...] = ()
    must_reduce_signal_codes: tuple[str, ...] = ()
    preserve_tokens: tuple[str, ...] = ()
    preserve_qualifiers: bool = False
    preserve_negations: bool = False
    max_edit_distance_ratio: float | None = None

    @classmethod
    def from_mapping(cls, payload: dict[str, Any] | None) -> "EvalExpectations":
        payload = payload or {}
        allow_signal_codes = tuple(str(code) for code in payload.get("allow_signal_codes", []))
        must_reduce_signal_codes = tuple(str(code) for code in payload.get("must_reduce_signal_codes", []))
        preserve_tokens = tuple(str(token) for token in payload.get("preserve_tokens", []))
        max_findings = payload.get("max_findings")
        max_edit_distance_ratio = payload.get("max_edit_distance_ratio")
        return cls(
            max_findings=int(max_findings) if max_findings is not None else None,
            allow_signal_codes=allow_signal_codes,
            must_reduce_signal_codes=must_reduce_signal_codes,
            preserve_tokens=preserve_tokens,
            preserve_qualifiers=bool(payload.get("preserve_qualifiers", False)),
            preserve_negations=bool(payload.get("preserve_negations", False)),
            max_edit_distance_ratio=(
                float(max_edit_distance_ratio) if max_edit_distance_ratio is not None else None
            ),
        )


@dataclass(frozen=True, slots=True)
class EvalCase:
    case_id: str
    task: str
    input_text: str
    genre: str | None = None
    mode: str = "minimal"
    profile_summary: str | None = None
    profile_traits: dict[str, str] | None = None
    expectations: EvalExpectations = EvalExpectations()

    @classmethod
    def from_path(cls, path: Path) -> "EvalCase":
        payload = json.loads(path.read_text(encoding="utf-8"))
        task = str(payload["task"]).strip().lower()
        if task not in {"analyze", "rewrite"}:
            raise ValueError(f"Unsupported eval task in {path}: {task}")
        profile_traits = payload.get("profile_traits") or None
        if profile_traits is not None:
            profile_traits = {str(code): str(value) for code, value in profile_traits.items()}
        return cls(
            case_id=str(payload["case_id"]),
            task=task,
            input_text=str(payload["input_text"]),
            genre=payload.get("genre"),
            mode=str(payload.get("mode", "minimal")),
            profile_summary=payload.get("profile_summary"),
            profile_traits=profile_traits,
            expectations=EvalExpectations.from_mapping(payload.get("expectations")),
        )


@dataclass(frozen=True, slots=True)
class EvalDataset:
    dataset_id: str
    version: str
    description: str
    cases: tuple[EvalCase, ...]


def load_dataset(path: str | Path) -> EvalDataset:
    """Load an evaluation dataset from a directory with manifest and case files."""
    root = Path(path)
    manifest_path = root / "manifest.json"
    cases_dir = root / "cases"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Evaluation manifest not found: {manifest_path}")
    if not cases_dir.is_dir():
        raise FileNotFoundError(f"Evaluation cases directory not found: {cases_dir}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    case_paths = sorted(child for child in cases_dir.iterdir() if child.is_file() and child.suffix == ".json")
    cases = tuple(EvalCase.from_path(case_path) for case_path in case_paths)
    return EvalDataset(
        dataset_id=str(manifest.get("dataset_id", root.name)),
        version=str(manifest.get("version", "0.1")),
        description=str(manifest.get("description", "")).strip(),
        cases=cases,
    )
