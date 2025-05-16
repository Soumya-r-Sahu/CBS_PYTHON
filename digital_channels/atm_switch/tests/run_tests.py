"""
ATM Switch Tests Runner

This script runs all tests for the ATM Switch module.
"""

import unittest
import sys
import os
from pathlib import Path

# Ensure the project root is in the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

# Import test modules
from tests.presentation.cli.test_atm_cli import AtmCliTests
from tests.integration.test_atm_integration import AtmIntegrationTests

if __name__ == "__main__":
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(AtmCliTests))
    test_suite.addTest(unittest.makeSuite(AtmIntegrationTests))
    
    # Run tests
    result = unittest.TextTestRunner(verbosity=2).run(test_suite)
    
    # Exit with appropriate status code
    sys.exit(0 if result.wasSuccessful() else 1)
