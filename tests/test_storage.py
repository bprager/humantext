import sqlite3
import sys
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from humantext.storage import HumanTextDatabase


class StorageTests(unittest.TestCase):
    def test_initialize_and_ingest_seed_database(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "state.db"
            database = HumanTextDatabase(db_path)
            try:
                database.initialize()
                document_id, analysis_id, analysis = database.ingest_and_analyze(
                    "Experts argue this pivotal moment reflects broader trends.\n\nOverall, it serves as a vibrant example.",
                    title="sample",
                )
                self.assertTrue(document_id.startswith("doc_"))
                self.assertTrue(analysis_id.startswith("analysis_"))
                self.assertGreaterEqual(len(analysis.findings), 4)
                self.assertGreaterEqual(len(database.list_rows("signal_definitions")), 30)
                self.assertGreaterEqual(len(database.list_rows("document_spans")), 3)
                self.assertEqual(len(database.list_rows("analysis_runs")), 1)
            finally:
                database.close()

            connection = sqlite3.connect(db_path)
            try:
                count = connection.execute("SELECT COUNT(*) FROM findings").fetchone()[0]
                self.assertGreater(count, 0)
            finally:
                connection.close()


if __name__ == "__main__":
    unittest.main()
