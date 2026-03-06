import subprocess
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENV = {"PYTHONPATH": str(ROOT / "src")}


class CliTests(unittest.TestCase):
    def test_analyze_command_runs(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "humantext.cli.main", "analyze", "Docs/demo.md"],
            cwd=ROOT,
            env=ENV,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(result.stdout.strip(), "[]")


if __name__ == "__main__":
    unittest.main()
