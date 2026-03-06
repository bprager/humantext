import io
import json
import sys
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

    def test_serve_stdio_round_trip(self) -> None:
        instream = io.StringIO(json.dumps({"id": 1, "tool": "server_metadata"}) + "\n")
        outstream = io.StringIO()
        serve_stdio(instream=instream, outstream=outstream)
        response = json.loads(outstream.getvalue().strip())
        self.assertTrue(response["ok"])
        self.assertEqual(response["result"]["version"], get_version())


if __name__ == "__main__":
    unittest.main()
