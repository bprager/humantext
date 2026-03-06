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

    def test_learn_style_persists_voice_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "state.db"
            database = HumanTextDatabase(db_path)
            try:
                database.initialize()
                profile = database.learn_style(
                    author_id="bernd",
                    profile_name="Bernd",
                    documents=[
                        {"text": "We review the record carefully. However, we keep the language direct.", "title": "a.txt"},
                        {"text": "The memo is concise, but it preserves nuance and context.", "title": "b.txt"},
                    ],
                )
                loaded = database.get_voice_profile(profile.profile_id)
                self.assertIsNotNone(loaded)
                assert loaded is not None
                self.assertEqual(loaded.author_id, "bernd")
                self.assertGreaterEqual(len(loaded.traits), 5)
                self.assertEqual(len(database.list_rows("voice_profiles")), 1)
                self.assertEqual(len(database.list_rows("voice_traits")), len(loaded.traits))
            finally:
                database.close()


if __name__ == "__main__":
    unittest.main()
