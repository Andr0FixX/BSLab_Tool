import unittest
import sys
import os

if __name__ == "__main__":
    test_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.abspath(os.path.join(test_dir, "..")))
    
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=test_dir, pattern="test_*.py")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print(f"\n==========================================")
        print(f"ALL TESTS PASSED! Total Tests: {result.testsRun}")
        print(f"==========================================")
        sys.exit(0)
    else:
        print(f"\n[FAILURES DETECTED] Failures: {len(result.failures)}, Errors: {len(result.errors)}")
        sys.exit(1)
