import unittest
import json
from app import create_app

class TestRoutes(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    # Test All 9 Multi-Page Website Portal Pages
    def test_page_1_home(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"MarketMind", resp.data)
        self.assertIn(b"Turn Shopping Data into", resp.data)

    def test_page_2_about(self):
        resp = self.client.get('/about')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Data Warehousing & Data Mining", resp.data)
        self.assertIn(b"Star Schema", resp.data)

    def test_page_3_dashboard(self):
        resp = self.client.get('/dashboard')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Executive Sales Analytics", resp.data)
        self.assertIn(b"Total Revenue", resp.data)

    def test_page_4_data_import(self):
        resp = self.client.get('/data-import')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Data Ingestion & Cleansing Portal", resp.data)
        self.assertIn(b"Run Complete ETL Pipeline", resp.data)

    def test_page_5_product_mining(self):
        resp = self.client.get('/product-mining')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Product Association Rule Mining", resp.data)
        self.assertIn(b"Minimum Support", resp.data)

    def test_page_6_customer_segmentation(self):
        resp = self.client.get('/customer-segmentation')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Customer RFM Segmentation", resp.data)
        self.assertIn(b"Number of Clusters", resp.data)

    def test_page_7_olap(self):
        resp = self.client.get('/olap')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"OLAP Multi-dimensional Analytics", resp.data)
        self.assertIn(b"Roll-Up", resp.data)

    def test_page_8_reports(self):
        resp = self.client.get('/reports')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Executive Reports", resp.data)

    def test_page_9_contact(self):
        resp = self.client.get('/contact')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Contact & Viva Feedback", resp.data)

    # Test REST API Endpoints
    def test_api_kpis(self):
        resp = self.client.get('/api/kpis')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue(data['success'])
        self.assertGreater(data['data']['total_revenue'], 0)

    def test_api_apriori(self):
        resp = self.client.get('/api/apriori?min_support=0.02&min_confidence=0.25')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue(data['success'])

    def test_api_kmeans(self):
        resp = self.client.get('/api/kmeans?k_clusters=4')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue(data['success'])

    def test_api_olap_rollup(self):
        resp = self.client.get('/api/olap/rollup?hierarchy=monthly')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue(data['success'])
        self.assertIn('sql_query', data['data'])

    def test_api_export_sales_report(self):
        resp = self.client.get('/api/export-report/sales')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, "text/csv; charset=utf-8")

    def test_api_download_template(self):
        resp = self.client.get('/api/download-template')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, "text/csv; charset=utf-8")

    def test_api_contact_submission(self):
        payload = {
            "name": "Unit Tester",
            "email": "test@university.edu",
            "category": "Viva Feedback",
            "subject": "Automated Test Subject",
            "message": "Testing contact database insertion endpoint.",
            "rating": 5
        }
        resp = self.client.post('/api/contact', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue(data['success'])

if __name__ == '__main__':
    unittest.main()
