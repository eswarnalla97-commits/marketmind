import os
import sys
import unittest

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def main():
    print("==================================================")
    print("Running MarketMind Comprehensive Test Suite")
    print("==================================================")
    loader = unittest.TestLoader()
    tests_dir = os.path.dirname(__file__)
    suite = loader.discover(tests_dir, pattern='test_*.py')
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    print("==================================================")
    if result.wasSuccessful():
        print(f"SUCCESS: All {result.testsRun} tests passed successfully!")
    else:
        print(f"FAILED: {len(result.failures)} failures, {len(result.errors)} errors out of {result.testsRun} tests.")
    print("==================================================")
    sys.exit(0 if result.wasSuccessful() else 1)

if __name__ == '__main__':
    main()
