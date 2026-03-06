import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from humantext.version import get_version

BASE_ENV = os.environ.copy()
BASE_ENV["PYTHONPATH"] = str(SRC)


class CliTests(unittest.TestCase):
    def test_analyze_command_runs(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "humantext.cli.main", "analyze", "Docs/demo.md"],
            cwd=ROOT,
            env=BASE_ENV,
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["findings"], [])

    def test_ingest_command_creates_database_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "humantext.db"
            sample_path = Path(tmpdir) / "sample.txt"
            sample_path.write_text("Experts argue this pivotal moment reflects broader trends.", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-m", "humantext.cli.main", "ingest", str(sample_path), "--db", str(db_path)],
                cwd=ROOT,
                env=BASE_ENV,
                capture_output=True,
                text=True,
                check=True,
            )
            payload = json.loads(result.stdout)
            self.assertIn("document_id", payload)
            self.assertIn("analysis_id", payload)
            self.assertTrue(db_path.exists())

    def test_version_command_matches_runtime_version(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "humantext.cli.main", "version"],
            cwd=ROOT,
            env=BASE_ENV,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(result.stdout.strip(), get_version())


if __name__ == "__main__":
    unittest.main()
