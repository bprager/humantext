import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from humantext.core.analysis import analyze_text
from humantext.rewrite.engine import rewrite_text
from humantext.llm.config import LLMConfig


class _FakeLLMClient:
    def rewrite_span(self, *, sentence: str, instructions: str) -> str:
        if "Additional critique to address" in instructions:
            return sentence.replace("reflects broader trends", "describes documented changes")
        return sentence.replace("pivotal moment", "specific milestone")

    def critique_rewrite(self, *, original_text: str, rewritten_text: str, instructions: str) -> list[str]:
        return ["The rewrite still sounds slightly generic."]


class _UnsafeLLMClient:
    def rewrite_span(self, *, sentence: str, instructions: str) -> str:
        return "This proves Paris handled it."

    def critique_rewrite(self, *, original_text: str, rewritten_text: str, instructions: str) -> list[str]:
        return []


class AnalysisTests(unittest.TestCase):
    def test_analyze_text_exposes_genre_and_profile_context(self) -> None:
        result = analyze_text(
            "Additionally, experts argue this pivotal moment reflects broader trends.",
            genre="technical memo",
            profile_id="profile_demo",
            profile_summary="Demo voice profile.",
        )
        payload = result.to_dict()
        self.assertEqual(payload["genre"], "technical memo")
        self.assertEqual(payload["profile_id"], "profile_demo")
        self.assertEqual(payload["profile_summary"], "Demo voice profile.")
        self.assertIn("Reviewed as technical memo.", payload["summary"])
        self.assertIn("Voice profile context loaded.", payload["summary"])
        self.assertTrue(all("genre_note" in finding for finding in payload["findings"]))
        self.assertTrue(any(finding["genre_note"] for finding in payload["findings"]))

    def test_analyze_text_returns_ranked_findings(self) -> None:
        result = analyze_text(
            "Additionally, experts argue this pivotal moment reflects broader trends."
        )
        self.assertEqual(result.top_signals[0], "VAGUE_ATTRIBUTION")
        self.assertEqual(result.findings[0].signal_code, "VAGUE_ATTRIBUTION")
        self.assertTrue(any(f.signal_code == "GENERIC_SIGNIFICANCE" for f in result.findings))
        self.assertIn("Detected", result.summary)

    def test_profile_traits_adjust_effective_scores(self) -> None:
        text = "This pivotal moment reflects broader trends."
        baseline = analyze_text(text)
        tuned = analyze_text(
            text,
            profile_summary="Trusted profile loaded.",
            profile_traits={"tolerance_for_abstraction": "high"},
        )

        def score_for(result: object, signal_code: str) -> float:
            findings = getattr(result, "findings")
            finding = next(item for item in findings if item.signal_code == signal_code)
            return finding.effective_score

        self.assertLess(
            score_for(tuned, "GENERIC_SIGNIFICANCE"),
            score_for(baseline, "GENERIC_SIGNIFICANCE"),
        )
        self.assertIn("Profile-aware scoring adjusted", tuned.summary)

    def test_rewrite_text_applies_strategy_rules(self) -> None:
        rewritten = rewrite_text(
            "Additionally, it is important to note that this vibrant platform serves as a pivotal moment."
        )
        self.assertIn("output_text", rewritten.to_dict())
        self.assertNotIn("Additionally,", rewritten.output_text)
        self.assertNotIn("important to note", rewritten.output_text.lower())
        self.assertNotIn("serves as", rewritten.output_text)
        self.assertNotIn("pivotal moment", rewritten.output_text.lower())
        self.assertTrue(rewritten.changes)

    def test_rewrite_text_handles_vague_attribution(self) -> None:
        rewritten = rewrite_text("Experts argue that this reflects broader trends.")
        self.assertNotIn("Experts argue", rewritten.output_text)
        self.assertIn("documented changes", rewritten.output_text)
        self.assertTrue(rewritten.output_text.startswith("This"))
        self.assertEqual(rewritten.warnings, [])

    def test_rewrite_text_returns_change_log(self) -> None:
        rewritten = rewrite_text(
            "Additionally, it is important to note that this vibrant platform serves as a pivotal moment."
        )
        payload = rewritten.to_dict()
        self.assertIn("change_log", payload)
        self.assertTrue(payload["change_log"])
        self.assertIn("explanation", payload["change_log"][0])

    def test_rewrite_text_can_use_optional_llm_for_flagged_spans(self) -> None:
        rewritten = rewrite_text(
            "This pivotal moment reflects broader trends. Keep this sentence unchanged.",
            llm_config=LLMConfig(
                provider="openai_compatible",
                base_url="http://localhost:9999",
                model="demo-model",
            ),
            llm_client=_FakeLLMClient(),
        )
        self.assertIn("specific milestone", rewritten.output_text)
        self.assertIn("describes documented changes", rewritten.output_text)
        self.assertIn("Keep this sentence unchanged.", rewritten.output_text)
        self.assertTrue(any(change.strategy == "llm_rewrite_span" for change in rewritten.changes))
        self.assertTrue(any(change.strategy == "llm_rewrite_second_pass" for change in rewritten.changes))
        self.assertTrue(any(item.source == "llm" for item in rewritten.critique))
        deterministic_items = [item for item in rewritten.critique if item.source == "deterministic" and item.signal_code]
        self.assertTrue(all(item.span_start is not None for item in deterministic_items))

    def test_rewrite_text_rejects_llm_rewrite_that_drops_guardrails(self) -> None:
        rewritten = rewrite_text(
            "This may not mark a shift for ACME 2026 results.",
            llm_config=LLMConfig(
                provider="openai_compatible",
                base_url="http://localhost:9999",
                model="demo-model",
            ),
            llm_client=_UnsafeLLMClient(),
        )
        self.assertIn("ACME 2026", rewritten.output_text)
        self.assertTrue(any("Rejected unsafe LLM rewrite" in warning for warning in rewritten.warnings))
        self.assertTrue(any(item.source == "deterministic" for item in rewritten.critique))


if __name__ == "__main__":
    unittest.main()
