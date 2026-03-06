import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from humantext.mcp import get_server_metadata
from humantext.version import get_version


class McpTests(unittest.TestCase):
    def test_server_metadata_reports_shared_version(self) -> None:
        metadata = get_server_metadata()
        self.assertEqual(metadata["name"], "humantext-mcp")
        self.assertEqual(metadata["version"], get_version())
        self.assertIn("rewrite_text", metadata["tools"])


if __name__ == "__main__":
    unittest.main()
