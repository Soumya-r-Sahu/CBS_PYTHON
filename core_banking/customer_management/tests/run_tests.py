"""
Customer Management Tests Runner

This script runs all tests for the Customer Management module.
"""

import unittest
import sys
import os
from pathlib import Path

# Ensure the project root is in the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

if __name__ == "__main__":
    # Discover and run all tests in the module
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(start_dir=os.path.dirname(__file__), pattern="test_*.py")
    
    # Run tests
    result = unittest.TextTestRunner(verbosity=2).run(test_suite)
    
    # Exit with appropriate status code
    sys.exit(0 if result.wasSuccessful() else 1)
