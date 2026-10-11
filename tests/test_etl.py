import unittest
import os
from config import config
from etl.etl_pipeline import validate_csv, run_etl, get_etl_history

class TestETL(unittest.TestCase):

    def test_validate_valid_csv(self):
        is_valid, msg, info = validate_csv(config.SAMPLE_DATA_PATH)
        self.assertTrue(is_valid, f"Validation failed: {msg}")
        self.assertEqual(len(info.get('missing_columns', [])), 0)

    def test_validate_nonexistent_csv(self):
        is_valid, msg, _ = validate_csv("non_existent_file.csv")
        self.assertFalse(is_valid)
        self.assertIn("not found", msg.lower())

    def test_etl_history_retrieval(self):
        history = get_etl_history(limit=5)
        self.assertIsInstance(history, list)
        self.assertGreaterEqual(len(history), 1, "At least one ETL batch run should be recorded in history.")
        self.assertIn("BatchID", history[0])
        self.assertIn("Status", history[0])

if __name__ == '__main__':
    unittest.main()
