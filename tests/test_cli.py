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

    def test_suggest_command_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_path = Path(tmpdir) / "sample.txt"
            sample_path.write_text("Experts argue this pivotal moment reflects broader trends.", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-m", "humantext.cli.main", "suggest", str(sample_path)],
                cwd=ROOT,
                env=BASE_ENV,
                capture_output=True,
                text=True,
                check=True,
            )
            payload = json.loads(result.stdout)
            self.assertTrue(payload["edit_plan"]["priorities"])

    def test_analyze_command_accepts_genre_and_profile_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            corpus = Path(tmpdir) / "corpus"
            corpus.mkdir()
            (corpus / "a.txt").write_text("We review the record carefully. However, we keep the language direct.", encoding="utf-8")
            (corpus / "b.md").write_text("The memo is concise, but it preserves nuance and context.", encoding="utf-8")
            db_path = Path(tmpdir) / "humantext.db"
            learned = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "humantext.cli.main",
                    "learn",
                    str(corpus),
                    "--db",
                    str(db_path),
                    "--author-id",
                    "bernd",
                    "--name",
                    "Bernd",
                ],
                cwd=ROOT,
                env=BASE_ENV,
                capture_output=True,
                text=True,
                check=True,
            )
            profile_id = json.loads(learned.stdout)["profile_id"]

            sample_path = Path(tmpdir) / "sample.txt"
            sample_path.write_text("Experts argue this pivotal moment reflects broader trends.", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "humantext.cli.main",
                    "analyze",
                    str(sample_path),
                    "--genre",
                    "technical memo",
                    "--profile-id",
                    profile_id,
                    "--db",
                    str(db_path),
                ],
                cwd=ROOT,
                env=BASE_ENV,
                capture_output=True,
                text=True,
                check=True,
            )
            payload = json.loads(result.stdout)
            self.assertEqual(payload["genre"], "technical memo")
            self.assertEqual(payload["profile_id"], profile_id)
            self.assertIn("profile_summary", payload)
            self.assertTrue(any(finding["genre_note"] for finding in payload["findings"]))

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

    def test_rewrite_command_returns_change_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_path = Path(tmpdir) / "sample.txt"
            sample_path.write_text(
                "Additionally, it is important to note that this vibrant platform serves as a pivotal moment.",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, "-m", "humantext.cli.main", "rewrite", str(sample_path)],
                cwd=ROOT,
                env=BASE_ENV,
                capture_output=True,
                text=True,
                check=True,
            )
            payload = json.loads(result.stdout)
            self.assertTrue(payload["change_log"])
            self.assertIn("explanation", payload["change_log"][0])

    def test_learn_command_persists_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            corpus = Path(tmpdir) / "corpus"
            corpus.mkdir()
            (corpus / "a.txt").write_text("We review the record carefully. However, we keep the language direct.", encoding="utf-8")
            (corpus / "b.md").write_text("The memo is concise, but it preserves nuance and context.", encoding="utf-8")
            db_path = Path(tmpdir) / "humantext.db"
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "humantext.cli.main",
                    "learn",
                    str(corpus),
                    "--db",
                    str(db_path),
                    "--author-id",
                    "bernd",
                    "--name",
                    "Bernd",
                ],
                cwd=ROOT,
                env=BASE_ENV,
                capture_output=True,
                text=True,
                check=True,
            )
            payload = json.loads(result.stdout)
            self.assertEqual(payload["author_id"], "bernd")
            self.assertTrue(payload["traits"])

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
