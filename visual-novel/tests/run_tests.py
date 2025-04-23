#!/usr/bin/env python

import unittest
import os
import sys

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import all test modules
from test_api_service import TestAPIService
from test_jlpt_curriculum import TestJLPTCurriculum
from test_progress_tracker import TestProgressTracker

def run_tests():
    # Create a test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestAPIService))
    test_suite.addTest(unittest.makeSuite(TestJLPTCurriculum))
    test_suite.addTest(unittest.makeSuite(TestProgressTracker))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Return the result
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)