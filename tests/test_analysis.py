import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from humantext.core.analysis import analyze_text
from humantext.rewrite.engine import rewrite_text


class AnalysisTests(unittest.TestCase):
    def test_analyze_text_returns_seeded_findings(self) -> None:
        findings = analyze_text("This facilitates change in order to scale.")
        self.assertEqual([item["signal_code"] for item in findings], ["GENERIC_PHRASE", "VERBOSITY"])

    def test_rewrite_text_applies_seeded_replacements(self) -> None:
        rewritten = rewrite_text("This facilitates change in order to scale.")
        self.assertEqual(rewritten, "This helps change to scale.")


if __name__ == "__main__":
    unittest.main()
