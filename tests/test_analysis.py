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
    def test_analyze_text_returns_ranked_findings(self) -> None:
        result = analyze_text(
            "Additionally, experts argue this pivotal moment reflects broader trends."
        )
        self.assertEqual(result.top_signals[0], "VAGUE_ATTRIBUTION")
        self.assertEqual(result.findings[0].signal_code, "VAGUE_ATTRIBUTION")
        self.assertTrue(any(f.signal_code == "GENERIC_SIGNIFICANCE" for f in result.findings))
        self.assertIn("Detected", result.summary)

    def test_rewrite_text_applies_strategy_rules(self) -> None:
        rewritten = rewrite_text(
            "Additionally, it is important to note that this vibrant platform serves as a pivotal moment."
        )
        self.assertIn("output_text", rewritten.to_dict())
        self.assertNotIn("Additionally,", rewritten.output_text)
        self.assertNotIn("important to note", rewritten.output_text.lower())
        self.assertNotIn("serves as", rewritten.output_text)
        self.assertTrue(rewritten.changes)


if __name__ == "__main__":
    unittest.main()
