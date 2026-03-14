import json
import io
import os
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
import unittest

ROOT = Path(__file__).resolve().parents[1]
if not (ROOT / "src" / "humantext").exists():
    ROOT = Path.cwd().resolve()
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from humantext.version import get_version
from humantext.cli.main import main as cli_main


class _Result:
    def __init__(self, stdout: str, returncode: int) -> None:
        self.stdout = stdout
        self.returncode = returncode


def _run_cli(*args: str, cwd: Path = ROOT) -> _Result:
    argv_before = sys.argv[:]
    cwd_before = Path.cwd()
    stdout_capture = io.StringIO()
    try:
        sys.argv = ["humantext", *args]
        os.chdir(cwd)
        with redirect_stdout(stdout_capture):
            try:
                code = cli_main()
            except SystemExit as exc:
                code = int(exc.code) if isinstance(exc.code, int) else 1
    finally:
        sys.argv = argv_before
        os.chdir(cwd_before)
    result = _Result(stdout=stdout_capture.getvalue(), returncode=code)
    if result.returncode != 0:
        raise AssertionError(
            "CLI command failed:\n"
            f"command: {['humantext', *args]}\n"
            f"stdout:\n{result.stdout}\n"
            f"returncode: {result.returncode}"
        )
    return result


class _StubRewriteResult:
    def to_dict(self) -> dict[str, object]:
        return {
            "output_text": "stub",
            "changes": [],
            "change_log": [],
            "critique": [],
            "warnings": [],
            "analysis": {"findings": []},
        }


class _StubArenaResult:
    def to_dict(self) -> dict[str, object]:
        return {
            "summary": "stub",
            "recommendation": "balanced",
            "recommendation_rationale": "stub rationale",
            "analysis": {"findings": []},
            "candidates": [],
        }


class CliTests(unittest.TestCase):
    def test_analyze_command_runs(self) -> None:
        result = _run_cli("analyze", "Docs/demo.md")
        payload = json.loads(result.stdout)
        self.assertEqual(payload["findings"], [])

    def test_suggest_command_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_path = Path(tmpdir) / "sample.txt"
            sample_path.write_text("Experts argue this pivotal moment reflects broader trends.", encoding="utf-8")
            result = _run_cli("suggest", str(sample_path))
            payload = json.loads(result.stdout)
            self.assertTrue(payload["edit_plan"]["priorities"])

    def test_analyze_command_accepts_genre_and_profile_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            corpus = Path(tmpdir) / "corpus"
            corpus.mkdir()
            (corpus / "a.txt").write_text("We review the record carefully. However, we keep the language direct.", encoding="utf-8")
            (corpus / "b.md").write_text("The memo is concise, but it preserves nuance and context.", encoding="utf-8")
            db_path = Path(tmpdir) / "humantext.db"
            learned = _run_cli(
                "learn",
                str(corpus),
                "--db",
                str(db_path),
                "--author-id",
                "bernd",
                "--name",
                "Bernd",
            )
            profile_id = json.loads(learned.stdout)["profile_id"]

            sample_path = Path(tmpdir) / "sample.txt"
            sample_path.write_text("Experts argue this pivotal moment reflects broader trends.", encoding="utf-8")
            result = _run_cli(
                "analyze",
                str(sample_path),
                "--genre",
                "technical memo",
                "--profile-id",
                profile_id,
                "--db",
                str(db_path),
            )
            payload = json.loads(result.stdout)
            self.assertEqual(payload["genre"], "technical memo")
            self.assertEqual(payload["profile_id"], profile_id)
            self.assertIn("profile_summary", payload)
            self.assertTrue(any(finding["genre_note"] for finding in payload["findings"]))
            self.assertTrue(any(finding["profile_adjustment"] != 0 for finding in payload["findings"]))

    def test_ingest_command_creates_database_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "humantext.db"
            sample_path = Path(tmpdir) / "sample.txt"
            sample_path.write_text("Experts argue this pivotal moment reflects broader trends.", encoding="utf-8")
            result = _run_cli("ingest", str(sample_path), "--db", str(db_path))
            payload = json.loads(result.stdout)
            self.assertIn("document_id", payload)
            self.assertIn("analysis_id", payload)
            self.assertTrue(db_path.exists())

    def test_rewrite_command_returns_change_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_path = Path(tmpdir) / "sample.txt"
            sample_path.write_text(
                "Additionally, it is important to note that this vibrant platform serves as a pivotal moment.",
                encoding="utf-8",
            )
            result = _run_cli("rewrite", str(sample_path))
            payload = json.loads(result.stdout)
            self.assertTrue(payload["change_log"])
            self.assertIn("explanation", payload["change_log"][0])

    def test_review_command_returns_candidates_and_recommendation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_path = Path(tmpdir) / "sample.txt"
            sample_path.write_text("Experts argue this pivotal moment reflects broader trends.", encoding="utf-8")
            result = _run_cli("review", str(sample_path))
            payload = json.loads(result.stdout)
            self.assertTrue(payload["candidates"])
            self.assertIn(payload["recommendation"], {candidate["candidate_id"] for candidate in payload["candidates"]})

    def test_rewrite_command_passes_optional_llm_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_path = Path(tmpdir) / "sample.txt"
            sample_path.write_text("This pivotal moment reflects broader trends.", encoding="utf-8")
            with patch("humantext.cli.main.rewrite_text", return_value=_StubRewriteResult()) as mocked_rewrite:
                _run_cli(
                    "rewrite",
                    str(sample_path),
                    "--llm-provider",
                    "openai_compatible",
                    "--llm-base-url",
                    "http://localhost:11434/v1",
                    "--llm-model",
                    "demo",
                )
            llm_config = mocked_rewrite.call_args.kwargs["llm_config"]
            self.assertIsNotNone(llm_config)
            assert llm_config is not None
            self.assertEqual(llm_config.provider, "openai_compatible")
            self.assertEqual(llm_config.base_url, "http://localhost:11434/v1")
            self.assertEqual(llm_config.model, "demo")
            self.assertTrue(llm_config.supports("critique_rewrite"))
            self.assertTrue(llm_config.supports("second_pass_rewrite"))

    def test_review_command_passes_optional_llm_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_path = Path(tmpdir) / "sample.txt"
            sample_path.write_text("This pivotal moment reflects broader trends.", encoding="utf-8")
            with patch("humantext.cli.main.review_rewrites", return_value=_StubArenaResult()) as mocked_review:
                _run_cli(
                    "review",
                    str(sample_path),
                    "--llm-provider",
                    "openai_compatible",
                    "--llm-base-url",
                    "http://localhost:11434/v1",
                    "--llm-model",
                    "demo",
                )
            llm_config = mocked_review.call_args.kwargs["llm_config"]
            self.assertIsNotNone(llm_config)
            assert llm_config is not None
            self.assertEqual(llm_config.provider, "openai_compatible")
            self.assertEqual(llm_config.base_url, "http://localhost:11434/v1")
            self.assertEqual(llm_config.model, "demo")

    def test_rewrite_command_loads_llm_defaults_from_dotenv(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cwd = Path(tmpdir)
            sample_path = cwd / "sample.txt"
            sample_path.write_text("This pivotal moment reflects broader trends.", encoding="utf-8")
            (cwd / ".env").write_text(
                "\n".join(
                    [
                        "HUMANTEXT_LLM_PROVIDER=openai_compatible",
                        "HUMANTEXT_LLM_BASE_URL=http://localhost:11434/v1",
                        "HUMANTEXT_LLM_MODEL=dotenv-model",
                        "HUMANTEXT_LLM_API_KEY_ENV=HT_TEST_KEY",
                        "HT_TEST_KEY=dotenv-secret",
                        "HUMANTEXT_LLM_TIMEOUT=45",
                        "HUMANTEXT_LLM_TEMPERATURE=0.35",
                        "HUMANTEXT_LLM_CAPABILITIES=rewrite_spans,critique_rewrite",
                    ]
                ),
                encoding="utf-8",
            )
            with patch.dict(os.environ, {}, clear=True):
                with patch("humantext.cli.main.rewrite_text", return_value=_StubRewriteResult()) as mocked_rewrite:
                    _run_cli("rewrite", str(sample_path), cwd=cwd)
            llm_config = mocked_rewrite.call_args.kwargs["llm_config"]
            self.assertIsNotNone(llm_config)
            assert llm_config is not None
            self.assertEqual(llm_config.provider, "openai_compatible")
            self.assertEqual(llm_config.base_url, "http://localhost:11434/v1")
            self.assertEqual(llm_config.model, "dotenv-model")
            self.assertEqual(llm_config.api_key_env, "HT_TEST_KEY")
            self.assertEqual(llm_config.api_key, "dotenv-secret")
            self.assertEqual(llm_config.timeout_seconds, 45)
            self.assertEqual(llm_config.temperature, 0.35)
            self.assertTrue(llm_config.supports("rewrite_spans"))
            self.assertTrue(llm_config.supports("critique_rewrite"))
            self.assertFalse(llm_config.supports("second_pass_rewrite"))

    def test_eval_command_writes_markdown_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.md"
            result = _run_cli(
                "eval",
                "data/datasets/core-v1",
                "--format",
                "markdown",
                "--output",
                str(output_path),
            )
            self.assertTrue(output_path.exists())
            report = output_path.read_text(encoding="utf-8")
            self.assertIn("# HumanText Evaluation Report", result.stdout)
            self.assertIn("`core-v1`", report)

    def test_rewrite_command_cli_values_override_dotenv(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cwd = Path(tmpdir)
            sample_path = cwd / "sample.txt"
            sample_path.write_text("This pivotal moment reflects broader trends.", encoding="utf-8")
            (cwd / ".env").write_text(
                "\n".join(
                    [
                        "HUMANTEXT_LLM_PROVIDER=openai_compatible",
                        "HUMANTEXT_LLM_BASE_URL=http://localhost:11434/v1",
                        "HUMANTEXT_LLM_MODEL=dotenv-model",
                    ]
                ),
                encoding="utf-8",
            )
            with patch.dict(os.environ, {}, clear=True):
                with patch("humantext.cli.main.rewrite_text", return_value=_StubRewriteResult()) as mocked_rewrite:
                    _run_cli(
                        "rewrite",
                        str(sample_path),
                        "--llm-provider",
                        "override-provider",
                        "--llm-base-url",
                        "http://127.0.0.1:9000/v1",
                        "--llm-model",
                        "override-model",
                        "--llm-capabilities",
                        "rewrite_spans,second_pass_rewrite",
                        cwd=cwd,
                    )
            llm_config = mocked_rewrite.call_args.kwargs["llm_config"]
            self.assertIsNotNone(llm_config)
            assert llm_config is not None
            self.assertEqual(llm_config.provider, "override-provider")
            self.assertEqual(llm_config.base_url, "http://127.0.0.1:9000/v1")
            self.assertEqual(llm_config.model, "override-model")
            self.assertTrue(llm_config.supports("second_pass_rewrite"))
            self.assertFalse(llm_config.supports("critique_rewrite"))

    def test_learn_command_persists_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            corpus = Path(tmpdir) / "corpus"
            corpus.mkdir()
            (corpus / "a.txt").write_text("We review the record carefully. However, we keep the language direct.", encoding="utf-8")
            (corpus / "b.md").write_text("The memo is concise, but it preserves nuance and context.", encoding="utf-8")
            db_path = Path(tmpdir) / "humantext.db"
            result = _run_cli(
                "learn",
                str(corpus),
                "--db",
                str(db_path),
                "--author-id",
                "bernd",
                "--name",
                "Bernd",
            )
            payload = json.loads(result.stdout)
            self.assertEqual(payload["author_id"], "bernd")
            self.assertTrue(payload["traits"])

    def test_version_command_matches_runtime_version(self) -> None:
        result = _run_cli("version")
        self.assertEqual(result.stdout.strip(), get_version())


if __name__ == "__main__":
    unittest.main()
