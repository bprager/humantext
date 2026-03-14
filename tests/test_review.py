import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from humantext.rewrite.arena import review_rewrites


class ReviewArenaTests(unittest.TestCase):
    def test_review_rewrites_returns_candidates_and_recommendation(self) -> None:
        result = review_rewrites("Experts argue this pivotal moment reflects broader trends.")
        payload = result.to_dict()
        self.assertGreaterEqual(len(payload["candidates"]), 3)
        self.assertIn(payload["recommendation"], {candidate["candidate_id"] for candidate in payload["candidates"]})
        self.assertIn("overall_score", payload["candidates"][0]["metrics"])

    def test_review_rewrites_adds_profile_match_candidate_when_traits_exist(self) -> None:
        result = review_rewrites(
            "Additionally, experts argue this pivotal moment reflects broader trends.",
            profile_summary="Measured, abstract style.",
            profile_traits={
                "tolerance_for_abstraction": "high",
                "directness": "measured",
                "transition_frequency": "0.16",
                "average_sentence_length": "18",
                "formality": "high",
            },
        )
        candidate_ids = {candidate.candidate_id for candidate in result.candidates}
        self.assertIn("profile_match", candidate_ids)


if __name__ == "__main__":
    unittest.main()
