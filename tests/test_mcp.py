import io
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from humantext.mcp import get_server_metadata, handle_tool_call, serve_stdio
from humantext.version import get_version


class McpTests(unittest.TestCase):
    def test_server_metadata_reports_shared_version(self) -> None:
        metadata = get_server_metadata()
        self.assertEqual(metadata["name"], "humantext-mcp")
        self.assertEqual(metadata["version"], get_version())
        self.assertIn("rewrite_text", metadata["tools"])
        self.assertIn("review_rewrites", metadata["tools"])

    def test_handle_tool_call_analyze_text(self) -> None:
        result = handle_tool_call("analyze_text", {"text": "Experts argue this pivotal moment reflects broader trends."})
        self.assertIn("findings", result)
        self.assertTrue(result["findings"])

    def test_handle_tool_call_suggest_edits(self) -> None:
        result = handle_tool_call("suggest_edits", {"text": "Experts argue this pivotal moment reflects broader trends."})
        self.assertTrue(result["edit_plan"]["priorities"])

    def test_handle_tool_call_rewrite_text_returns_change_log(self) -> None:
        result = handle_tool_call(
            "rewrite_text",
            {"text": "Additionally, it is important to note that this vibrant platform serves as a pivotal moment."},
        )
        self.assertTrue(result["change_log"])
        self.assertIn("explanation", result["change_log"][0])

    def test_handle_tool_call_review_rewrites_returns_candidates(self) -> None:
        result = handle_tool_call(
            "review_rewrites",
            {"text": "Experts argue this pivotal moment reflects broader trends."},
        )
        self.assertTrue(result["candidates"])
        self.assertIn(result["recommendation"], {candidate["candidate_id"] for candidate in result["candidates"]})

    def test_handle_tool_call_rewrite_text_accepts_llm_config(self) -> None:
        with patch("humantext.mcp.server.rewrite_text") as mocked_rewrite:
            mocked_rewrite.return_value.to_dict.return_value = {
                "output_text": "stub",
                "changes": [],
                "change_log": [],
                "critique": [],
                "warnings": [],
                "analysis": {"findings": []},
            }
            handle_tool_call(
                "rewrite_text",
                {
                    "text": "This pivotal moment reflects broader trends.",
                    "llm": {
                        "provider": "openai_compatible",
                        "base_url": "http://localhost:11434/v1",
                        "model": "demo",
                    },
                },
            )
            llm_config = mocked_rewrite.call_args.kwargs["llm_config"]
            self.assertIsNotNone(llm_config)
            assert llm_config is not None
            self.assertEqual(llm_config.provider, "openai_compatible")
            self.assertEqual(llm_config.model, "demo")
            self.assertTrue(llm_config.supports("critique_rewrite"))
            self.assertTrue(llm_config.supports("second_pass_rewrite"))

    def test_handle_tool_call_rewrite_text_loads_llm_defaults_from_dotenv(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cwd_before = Path.cwd()
            cwd = Path(tmpdir)
            (cwd / ".env").write_text(
                "\n".join(
                    [
                        "HUMANTEXT_LLM_PROVIDER=openai_compatible",
                        "HUMANTEXT_LLM_BASE_URL=http://localhost:11434/v1",
                        "HUMANTEXT_LLM_MODEL=dotenv-model",
                        "HUMANTEXT_LLM_API_KEY_ENV=HT_TEST_KEY",
                        "HT_TEST_KEY=dotenv-secret",
                    ]
                ),
                encoding="utf-8",
            )
            try:
                os.chdir(cwd)
                with patch.dict(os.environ, {}, clear=True):
                    with patch("humantext.mcp.server.rewrite_text") as mocked_rewrite:
                        mocked_rewrite.return_value.to_dict.return_value = {
                            "output_text": "stub",
                            "changes": [],
                            "change_log": [],
                            "critique": [],
                            "warnings": [],
                            "analysis": {"findings": []},
                        }
                        handle_tool_call("rewrite_text", {"text": "This pivotal moment reflects broader trends."})
                llm_config = mocked_rewrite.call_args.kwargs["llm_config"]
            finally:
                os.chdir(cwd_before)
            self.assertIsNotNone(llm_config)
            assert llm_config is not None
            self.assertEqual(llm_config.provider, "openai_compatible")
            self.assertEqual(llm_config.model, "dotenv-model")
            self.assertEqual(llm_config.api_key, "dotenv-secret")

    def test_handle_tool_call_learn_and_get_voice_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "humantext.db")
            learned = handle_tool_call(
                "learn_style",
                {
                    "author_id": "bernd",
                    "name": "Bernd",
                    "db_path": db_path,
                    "documents": [
                        {"text": "We review the record carefully. However, we keep the language direct.", "title": "a.txt"},
                        {"text": "The memo is concise, but it preserves nuance and context.", "title": "b.txt"},
                    ],
                },
            )
            loaded = handle_tool_call("get_voice_profile", {"db_path": db_path, "profile_id": learned["profile_id"]})
            self.assertEqual(loaded["profile_id"], learned["profile_id"])
            self.assertTrue(loaded["traits"])

            analyzed = handle_tool_call(
                "analyze_text",
                {
                    "text": "Experts argue this pivotal moment reflects broader trends.",
                    "genre": "technical memo",
                    "profile_id": learned["profile_id"],
                    "db_path": db_path,
                },
            )
            self.assertEqual(analyzed["genre"], "technical memo")
            self.assertEqual(analyzed["profile_id"], learned["profile_id"])
            self.assertIn("profile_summary", analyzed)
            self.assertTrue(any(finding["genre_note"] for finding in analyzed["findings"]))
            self.assertTrue(any(finding["profile_adjustment"] != 0 for finding in analyzed["findings"]))

    def test_serve_stdio_round_trip(self) -> None:
        instream = io.StringIO(json.dumps({"id": 1, "tool": "server_metadata"}) + "\n")
        outstream = io.StringIO()
        serve_stdio(instream=instream, outstream=outstream)
        response = json.loads(outstream.getvalue().strip())
        self.assertTrue(response["ok"])
        self.assertEqual(response["result"]["version"], get_version())


if __name__ == "__main__":
    unittest.main()
