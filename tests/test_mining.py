import unittest
from mining.apriori_miner import run_apriori_mining
from mining.kmeans_segmenter import run_customer_segmentation

class TestDataMining(unittest.TestCase):

    def test_apriori_execution(self):
        res = run_apriori_mining(min_support=0.02, min_confidence=0.25)
        self.assertTrue(res['success'], f"Apriori failed: {res.get('message')}")
        self.assertGreater(res['total_transactions'], 0)
        self.assertGreaterEqual(res['rules_count'], 0)
        self.assertIn('top_combinations', res)
        self.assertIn('rules', res)

    def test_kmeans_execution(self):
        res = run_customer_segmentation(k_clusters=4)
        self.assertTrue(res['success'], f"K-Means failed: {res.get('message')}")
        self.assertEqual(res['k_clusters'], 4)
        self.assertGreater(res['total_customers'], 0)
        self.assertEqual(len(res['clusters']), 4)
        self.assertGreater(len(res['customers']), 0)

        # Check cluster fields
        c0 = res['clusters'][0]
        self.assertIn('name', c0)
        self.assertIn('avg_spend', c0)
        self.assertIn('customer_count', c0)

    def test_kmeans_variable_k(self):
        for k in [2, 3, 5]:
            res = run_customer_segmentation(k_clusters=k)
            self.assertTrue(res['success'])
            self.assertEqual(len(res['clusters']), k)

if __name__ == '__main__':
    unittest.main()
