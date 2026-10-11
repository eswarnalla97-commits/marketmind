import unittest
from database.db_manager import get_db_connection, get_warehouse_stats, query_scalar

class TestWarehouse(unittest.TestCase):

    def test_database_connection(self):
        conn = get_db_connection()
        self.assertIsNotNone(conn)
        conn.close()

    def test_star_schema_tables_exist(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        expected_tables = [
            'FactSales', 'DimDate', 'DimProduct', 'DimCustomer', 
            'DimOrder', 'StagingTransactions', 'ETLHistory', 'FeedbackSubmissions'
        ]
        for t in expected_tables:
            self.assertIn(t, tables, f"Expected table {t} missing from Star Schema database.")

    def test_warehouse_has_data(self):
        stats = get_warehouse_stats()
        self.assertGreater(stats.get('FactSales', 0), 0, "FactSales should have seeded rows.")
        self.assertGreater(stats.get('DimCustomer', 0), 0, "DimCustomer should have seeded rows.")
        self.assertGreater(stats.get('DimProduct', 0), 0, "DimProduct should have seeded rows.")
        self.assertGreater(stats.get('DimDate', 0), 0, "DimDate should have seeded rows.")
        self.assertGreater(stats.get('DimOrder', 0), 0, "DimOrder should have seeded rows.")

    def test_fact_grain_no_negative_values(self):
        negative_rev = query_scalar("SELECT COUNT(*) FROM FactSales WHERE TotalAmount < 0 OR Quantity <= 0")
        self.assertEqual(negative_rev, 0, "FactSales must not contain invalid negative revenue or non-positive quantities.")

if __name__ == '__main__':
    unittest.main()
