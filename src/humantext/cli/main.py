"""Standard-library CLI for HumanText."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from humantext.core.analysis import analyze_text
from humantext.core.suggest import suggest_edits
from humantext.eval import render_markdown_report, run_evaluation
from humantext.llm.config import LLMConfig
from humantext.mcp import serve_stdio
from humantext.rewrite.arena import review_rewrites
from humantext.rewrite.engine import rewrite_text
from humantext.storage.database import HumanTextDatabase
from humantext.version import get_version


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _emit_output(text: str, output_path: Path | None = None) -> None:
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
    print(text)


def _load_profile_context(db_path: Path, profile_id: str | None) -> tuple[str | None, dict[str, str] | None]:
    if not profile_id:
        return None, None

    database = HumanTextDatabase(db_path)
    try:
        database.initialize()
        profile = database.get_voice_profile(profile_id)
    finally:
        database.close()

    if profile is None:
        raise ValueError(f"Unknown profile_id: {profile_id}")
    traits = {trait.trait_code: trait.trait_value for trait in profile.traits}
    return profile.profile_summary, traits


def _analysis_kwargs(parser: argparse.ArgumentParser, args: argparse.Namespace) -> dict[str, object | None]:
    profile_id = getattr(args, "profile_id", None)
    db_path = getattr(args, "db", Path("humantext.db"))
    try:
        profile_summary, profile_traits = _load_profile_context(db_path, profile_id)
    except ValueError as exc:
        parser.error(str(exc))
    return {
        "genre": getattr(args, "genre", None),
        "profile_id": profile_id,
        "profile_summary": profile_summary,
        "profile_traits": profile_traits,
    }


def _llm_kwargs(args: argparse.Namespace) -> dict[str, object | None]:
    capabilities = getattr(args, "llm_capabilities", "rewrite_spans,critique_rewrite,second_pass_rewrite")
    config = LLMConfig.from_mapping(
        {
            "provider": getattr(args, "llm_provider", None),
            "base_url": getattr(args, "llm_base_url", None),
            "model": getattr(args, "llm_model", None),
            "api_key_env": getattr(args, "llm_api_key_env", None),
            "timeout_seconds": getattr(args, "llm_timeout", None),
            "temperature": getattr(args, "llm_temperature", None),
            "enabled_capabilities": capabilities,
        }
    )
    return {"llm_config": config}


def _add_llm_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--llm-provider")
    parser.add_argument("--llm-base-url")
    parser.add_argument("--llm-model")
    parser.add_argument("--llm-api-key-env")
    parser.add_argument("--llm-timeout", type=int)
    parser.add_argument("--llm-temperature", type=float)
    parser.add_argument("--llm-capabilities")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="humantext", description="HumanText CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_parser = subparsers.add_parser("analyze", help="Analyze a document")
    analyze_parser.add_argument("file", type=Path)
    analyze_parser.add_argument("--genre")
    analyze_parser.add_argument("--profile-id")
    analyze_parser.add_argument("--db", type=Path, default=Path("humantext.db"))

    suggest_parser = subparsers.add_parser("suggest", help="Suggest ranked edits for a document")
    suggest_parser.add_argument("file", type=Path)
    suggest_parser.add_argument("--genre")
    suggest_parser.add_argument("--profile-id")
    suggest_parser.add_argument("--db", type=Path, default=Path("humantext.db"))

    review_parser = subparsers.add_parser("review", help="Compare rewrite arena candidates for a document")
    review_parser.add_argument("file", type=Path)
    review_parser.add_argument("--genre")
    review_parser.add_argument("--profile-id")
    review_parser.add_argument("--db", type=Path, default=Path("humantext.db"))
    _add_llm_arguments(review_parser)

    rewrite_parser = subparsers.add_parser("rewrite", help="Rewrite a document")
    rewrite_parser.add_argument("file", type=Path)
    rewrite_parser.add_argument("--genre")
    rewrite_parser.add_argument("--profile-id")
    rewrite_parser.add_argument("--db", type=Path, default=Path("humantext.db"))
    _add_llm_arguments(rewrite_parser)

    ingest_parser = subparsers.add_parser("ingest", help="Ingest and analyze a document into SQLite")
    ingest_parser.add_argument("file", type=Path)
    ingest_parser.add_argument("--genre")
    ingest_parser.add_argument("--profile-id")
    ingest_parser.add_argument("--db", type=Path, default=Path("humantext.db"))

    eval_parser = subparsers.add_parser("eval", help="Run a benchmark dataset")
    eval_parser.add_argument("path", type=Path)
    eval_parser.add_argument("--format", choices=("json", "markdown"), default="json")
    eval_parser.add_argument("--output", type=Path)
    _add_llm_arguments(eval_parser)

    subparsers.add_parser("version", help="Print the current HumanText version")
    subparsers.add_parser("mcp-serve", help="Serve HumanText tools over newline-delimited JSON on stdio")

    learn_parser = subparsers.add_parser("learn", help="Learn a voice profile from a trusted corpus directory")
    learn_parser.add_argument("path", type=Path)
    learn_parser.add_argument("--db", type=Path, default=Path("humantext.db"))
    learn_parser.add_argument("--author-id", required=True)
    learn_parser.add_argument("--name")

    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "analyze":
        _emit_output(json.dumps(analyze_text(_read_text(args.file), **_analysis_kwargs(parser, args)).to_dict(), indent=2))
        return 0

    if args.command == "suggest":
        _emit_output(json.dumps(suggest_edits(_read_text(args.file), **_analysis_kwargs(parser, args)).to_dict(), indent=2))
        return 0

    if args.command == "review":
        review_kwargs = _analysis_kwargs(parser, args)
        review_kwargs.update(_llm_kwargs(args))
        _emit_output(json.dumps(review_rewrites(_read_text(args.file), **review_kwargs).to_dict(), indent=2))
        return 0

    if args.command == "rewrite":
        rewrite_kwargs = _analysis_kwargs(parser, args)
        rewrite_kwargs.update(_llm_kwargs(args))
        _emit_output(json.dumps(rewrite_text(_read_text(args.file), **rewrite_kwargs).to_dict(), indent=2))
        return 0

    if args.command == "ingest":
        database = HumanTextDatabase(args.db)
        try:
            database.initialize()
            analysis_kwargs = _analysis_kwargs(parser, args)
            document_id, analysis_id, analysis = database.ingest_and_analyze(
                _read_text(args.file),
                path=str(args.file),
                title=args.file.name,
                **analysis_kwargs,
            )
        finally:
            database.close()
        _emit_output(json.dumps({"document_id": document_id, "analysis_id": analysis_id, "summary": analysis.summary}, indent=2))
        return 0

    if args.command == "eval":
        result = run_evaluation(str(args.path), **_llm_kwargs(args))
        rendered = render_markdown_report(result) if args.format == "markdown" else json.dumps(result.to_dict(), indent=2)
        _emit_output(rendered, args.output)
        return 0

    if args.command == "version":
        _emit_output(get_version())
        return 0

    if args.command == "mcp-serve":
        return serve_stdio()

    if args.command == "learn":
        database = HumanTextDatabase(args.db)
        try:
            database.initialize()
            documents = [
                {
                    "text": child.read_text(encoding="utf-8"),
                    "path": str(child),
                    "title": child.name,
                    "source_type": child.suffix.lstrip(".") or "text",
                }
                for child in sorted(args.path.rglob("*"))
                if child.is_file() and child.suffix.lower() in {".md", ".txt"}
            ]
            profile = database.learn_style(author_id=args.author_id, documents=documents, profile_name=args.name)
        finally:
            database.close()
        _emit_output(json.dumps(profile.to_dict(), indent=2))
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
