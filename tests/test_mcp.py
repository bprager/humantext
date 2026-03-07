import io
import json
import sys
import tempfile
from pathlib import Path
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
