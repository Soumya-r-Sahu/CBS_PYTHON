# CBS_PYTHON Test System

## Overview

The CBS_PYTHON test system is designed to ensure the quality, reliability, and correctness of the Core Banking System. This document describes the structure, organization, and implementation of the test system.

## Test Categories

The test system is organized into three main categories as defined in the Test_guide.md:

### Unit Tests

Unit tests verify that individual components work correctly in isolation. They focus on testing the functionality of specific functions, classes, or modules without relying on external dependencies. Unit tests are located in the `Tests/unit` directory.

Key characteristics:
- Fast execution
- No external dependencies (databases, APIs, etc.)
- Mocked external dependencies
- Focus on a single component

### Integration Tests

Integration tests verify that multiple components work correctly together. They test the interaction between different modules, services, or subsystems. Integration tests are located in the `Tests/integration` directory.

Key characteristics:
- Test interaction between components
- May require some external dependencies
- Focus on interfaces between components
- Verify correct data flow between components

### End-to-End Tests

End-to-end (E2E) tests verify that the entire system works correctly from a user's perspective. They simulate real-world scenarios by testing complete workflows. E2E tests are located in the `Tests/e2e` directory.

Key characteristics:
- Test complete user workflows
- Require the full system to be running
- Simulate real-world scenarios
- Verify system behavior from a user's perspective

## Test Implementation

### Test File Structure

Each test file follows a standard structure:

```python
"""
Core Banking System - [Test Category] [Feature] Tests

This module contains [test category] tests for [feature].
[Additional description]
"""

import pytest
import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Import modules to test
from module.to.test import Class, function

class TestFeature(unittest.TestCase):
    """[Test category] tests for [feature]."""
    
    def setUp(self):
        """Set up test environment."""
        # Setup code
    
    def tearDown(self):
        """Clean up after each test."""
        # Cleanup code
    
    def test_specific_functionality(self):
        """Test [specific functionality]."""
        # Test code
        result = function()
        self.assertEqual(result, expected_value)
```

### Test Fixtures

Common test fixtures are defined in `Tests/conftest.py`. These fixtures provide reusable test data and utilities that can be used across multiple test files.

Key fixtures include:
- Database connections
- Sample customer data
- Sample account data
- Sample transaction data
- API client
- Module registry
- Service registry
- Health check data

### Running Tests

Tests can be run using the `Tests/run_tests.py` script, which provides a flexible command-line interface for running specific test categories or all tests together.

```bash
# Run all tests
python -m Tests.run_tests --all

# Run specific test categories
python -m Tests.run_tests --unit
python -m Tests.run_tests --integration
python -m Tests.run_tests --e2e

# Generate coverage report
python -m Tests.run_tests --all --coverage

# Generate test report
python -m Tests.run_tests --all --report test_report.html
```

## Module Health Check Tests

A key part of the test system is the module health check tests, which verify that all modules report their health status correctly. These tests ensure that the system can detect and report issues with dependencies, services, and database connections.

### Health Check Structure

Each module implements the `_perform_health_check` method, which returns health status information in a standardized format:

```python
{
    "module_name": "module_name",
    "version": "1.0.0",
    "timestamp": "2023-01-01T12:00:00.000Z",
    "status": "active",
    "checks": [
        {
            "name": "check_name",
            "status": "healthy|degraded|critical",
            "message": "Human-readable status message"
        }
    ],
    "dependencies_status": "healthy|degraded|critical",
    "services_status": "healthy|degraded|critical",
    "database_status": "healthy|degraded|critical",
    "overall_status": "healthy|degraded|critical"
}
```

### Health Check Tests

Health check tests verify that:
- Modules report their health status correctly
- Dependency issues are detected and reported
- Service registration issues are detected and reported
- Database connection issues are detected and reported

## Coverage Reports

Test coverage reports can be generated using the `--coverage` option when running tests. These reports show which parts of the code are covered by tests and which are not, helping to identify areas that need additional testing.

Coverage reports are generated in HTML format and can be viewed in a web browser by opening the `htmlcov/index.html` file.

## Adding New Tests

When adding new tests, follow these guidelines:

1. Place the test file in the appropriate directory (`unit`, `integration`, or `e2e`)
2. Follow the standard test file structure
3. Use fixtures from `conftest.py` where applicable
4. Ensure tests clean up after themselves
5. Add appropriate docstrings and comments
6. Make sure tests are independent and can run in any order

## Conclusion

The CBS_PYTHON test system provides a comprehensive framework for testing all aspects of the Core Banking System. By organizing tests into categories and following a standardized approach, we ensure that the system is thoroughly tested and meets all requirements.
