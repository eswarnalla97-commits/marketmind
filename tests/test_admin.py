import unittest
import json
from app import create_app
from database.db_manager import query_scalar

class TestAdmin(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def login_as(self, username, password):
        """Helper to log in as a specific user."""
        return self.client.post('/admin/login', data={
            'username': username,
            'password': password
        }, follow_redirects=False)

    def test_admin_login_success(self):
        resp = self.login_as('admin', 'Admin@MarketMind2024')
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/admin', resp.headers['Location'])

    def test_admin_login_failure(self):
        resp = self.client.post('/admin/login', data={
            'username': 'admin',
            'password': 'WrongPassword123'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Invalid username/email or password", resp.data)

    def test_unauthenticated_admin_access_redirects(self):
        resp = self.client.get('/admin/dashboard')
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/admin/login', resp.headers['Location'])

    def test_unauthenticated_api_returns_401(self):
        resp = self.client.get('/api/admin/metrics')
        self.assertEqual(resp.status_code, 401)
        data = json.loads(resp.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['code'], 'UNAUTHORIZED')

    def test_admin_views_with_auth(self):
        with self.client:
            self.login_as('admin', 'Admin@MarketMind2024')
            
            # 1. Cockpit Dashboard
            resp = self.client.get('/admin/dashboard')
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"Administrative Control Center", resp.data)
            
            # 2. Users View
            resp = self.client.get('/admin/users')
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"User & Role Management", resp.data)
            
            # 3. Orders View
            resp = self.client.get('/admin/orders')
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"Orders & Invoices Management", resp.data)
            
            # 4. Products View
            resp = self.client.get('/admin/products')
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"Product Catalog", resp.data)

            # 5. ETL Management View
            resp = self.client.get('/admin/etl-management')
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"ETL Pipeline & Staging Isolation", resp.data)

            # 6. Feedback View
            resp = self.client.get('/admin/feedback')
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"Viva Evaluator", resp.data)

            # 7. Reports View
            resp = self.client.get('/admin/reports')
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"System Audit Trail", resp.data)

            # 8. Settings View
            resp = self.client.get('/admin/settings')
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"System Configurations & Profile Settings", resp.data)

    def test_role_based_access_control(self):
        # Analyst should have access to read metrics, but 403 when creating users
        with self.client:
            self.login_as('analyst_priya', 'Priya@2024')

            # Can view dashboard
            resp = self.client.get('/admin/dashboard')
            self.assertEqual(resp.status_code, 200)

            # Attempting to create user should be forbidden (403)
            resp = self.client.post('/api/admin/users', json={
                'username': 'hacker',
                'email': 'hacker@test.com',
                'password': 'Password123',
                'full_name': 'Hacker'
            })
            self.assertEqual(resp.status_code, 403)
            data = json.loads(resp.data)
            self.assertFalse(data['success'])
            self.assertEqual(data['code'], 'FORBIDDEN')

    def test_user_crud_operations(self):
        with self.client:
            self.login_as('admin', 'Admin@MarketMind2024')

            # 1. Create User
            test_username = 'test_analyst_qa'
            resp = self.client.post('/api/admin/users', json={
                'username': test_username,
                'email': 'qa_analyst@marketmind.internal',
                'password': 'TestPassword@123',
                'full_name': 'QA Test Analyst',
                'role': 'Analyst',
                'status': 'Active'
            })
            self.assertEqual(resp.status_code, 200)
            data = json.loads(resp.data)
            self.assertTrue(data['success'])

            # 2. Get Users List
            resp = self.client.get('/api/admin/users?q=test_analyst_qa')
            self.assertEqual(resp.status_code, 200)
            data = json.loads(resp.data)
            self.assertTrue(data['success'])
            self.assertGreaterEqual(len(data['data']['users']), 1)
            user_id = data['data']['users'][0]['UserID']

            # 3. Toggle Status
            resp = self.client.post(f'/api/admin/users/{user_id}/toggle-status')
            self.assertEqual(resp.status_code, 200)

            # 4. Update User
            resp = self.client.put(f'/api/admin/users/{user_id}', json={
                'full_name': 'QA Analyst Senior',
                'email': 'qa_senior@marketmind.internal',
                'role': 'Analyst',
                'status': 'Active'
            })
            self.assertEqual(resp.status_code, 200)

            # 5. Delete User
            resp = self.client.delete(f'/api/admin/users/{user_id}')
            self.assertEqual(resp.status_code, 200)

    def test_order_status_update(self):
        with self.client:
            self.login_as('admin', 'Admin@MarketMind2024')

            # Get first order
            order_key = query_scalar("SELECT OrderKey FROM DimOrder LIMIT 1")
            if order_key:
                resp = self.client.put(f'/api/admin/orders/{order_key}/status', json={'status': 'Shipped'})
                self.assertEqual(resp.status_code, 200)
                data = json.loads(resp.data)
                self.assertTrue(data['success'])

                # Test order details
                resp = self.client.get(f'/api/admin/orders/{order_key}')
                self.assertEqual(resp.status_code, 200)
                data = json.loads(resp.data)
                self.assertTrue(data['success'])
                self.assertIn('items', data['data'])

    def test_product_crud_operations(self):
        with self.client:
            self.login_as('admin', 'Admin@MarketMind2024')

            test_sku = 'TEST-SKU-999'
            resp = self.client.post('/api/admin/products', json={
                'product_id': test_sku,
                'product_name': 'Test Mechanical Keyboard',
                'category': 'Electronics',
                'unit_price': 1899.00
            })
            self.assertEqual(resp.status_code, 200)
            data = json.loads(resp.data)
            self.assertTrue(data['success'])

            # Find created product
            prod_key = query_scalar("SELECT ProductKey FROM DimProduct WHERE ProductID = ?", (test_sku,))
            self.assertIsNotNone(prod_key)

            # Update product
            resp = self.client.put(f'/api/admin/products/{prod_key}', json={
                'product_name': 'Test Mechanical Keyboard RGB',
                'category': 'Electronics',
                'unit_price': 2199.00
            })
            self.assertEqual(resp.status_code, 200)

            # Delete product
            resp = self.client.delete(f'/api/admin/products/{prod_key}')
            self.assertEqual(resp.status_code, 200)

    def test_audit_logs_and_export(self):
        with self.client:
            self.login_as('admin', 'Admin@MarketMind2024')

            resp = self.client.get('/api/admin/export-audit')
            self.assertEqual(resp.status_code, 200)
            self.assertIn("text/csv", resp.content_type)
            self.assertIn(b"LogID", resp.data)

    def test_quick_login_redirects_and_authenticates(self):
        resp = self.client.get('/admin/quick-login', follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Control Center", resp.data)
        self.assertIn(b"admin", resp.data)

if __name__ == '__main__':
    unittest.main()
