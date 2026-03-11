import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from humantext.eval import render_markdown_report, run_evaluation


DATASET = ROOT / "data" / "datasets" / "core-v1"


class EvalTests(unittest.TestCase):
    def test_run_evaluation_core_dataset_passes(self) -> None:
        result = run_evaluation(str(DATASET))
        payload = result.to_dict()
        self.assertEqual(payload["dataset_id"], "core-v1")
        self.assertEqual(payload["aggregate_metrics"]["total_cases"], 6)
        self.assertEqual(payload["aggregate_metrics"]["passed_cases"], 6)
        self.assertTrue(all(case_result["passed"] for case_result in payload["case_results"]))

    def test_render_markdown_report_includes_case_rows(self) -> None:
        report = render_markdown_report(run_evaluation(str(DATASET)))
        self.assertIn("# HumanText Evaluation Report", report)
        self.assertIn("`core-v1`", report)
        self.assertIn("`rewrite-genericity-001`", report)


if __name__ == "__main__":
    unittest.main()
