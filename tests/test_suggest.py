import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from humantext.core.suggest import suggest_edits


class SuggestTests(unittest.TestCase):
    def test_suggest_edits_returns_ranked_priorities_and_samples(self) -> None:
        text = "Experts argue this pivotal moment reflects broader trends."
        suggestion = suggest_edits(text)
        self.assertTrue(suggestion.edit_plan)
        self.assertEqual(suggestion.edit_plan[0].signal_code, "VAGUE_ATTRIBUTION")
        self.assertTrue(suggestion.sample_edits)
        self.assertEqual(suggestion.sample_edits[0]["signal_code"], "VAGUE_ATTRIBUTION")
        self.assertNotEqual(suggestion.sample_edits[0]["before"], text)


if __name__ == "__main__":
    unittest.main()
