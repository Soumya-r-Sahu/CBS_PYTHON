# tests/__init__.py
"""
Core Banking System - Test Suite

This package contains all tests for the Core Banking System.
The tests are organized into the following categories:

1. unit: 
   - Tests individual components in isolation
   - Fast execution with minimal dependencies
   - Uses mocks and stubs for external systems
   - Includes database unit tests with mocking
   
2. integration: 
   - Tests how components work together
   - Verifies correct interactions between modules
   - Includes database integration tests and API endpoint tests
   - May require actual database connections
   
3. e2e: 
   - End-to-end tests for complete workflows
   - Tests the system as a user would experience it
   - Simulates real-world scenarios and use cases
   - Includes database workflow tests and API flow tests
   - Note: API tests require the API server to be running

To run all tests, use the run_tests.py script:
    python -m tests.run_tests --all

For specific test categories:
    python -m tests.run_tests --unit
    python -m tests.run_tests --integration
    python -m tests.run_tests --database
    python -m tests.run_tests --api
    python -m tests.run_tests --e2e
"""
