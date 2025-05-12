# Core Banking System Test Suite

This directory contains the test suite for the Core Banking System.

## Test Categories

The tests are organized into the following categories:

### 1. Unit Tests (`unit/`)
Testing individual components in isolation, with dependencies mocked or stubbed.
- Database unit tests (mocked)
- Model unit tests
- Utility function tests

### 2. Integration Tests (`integration/`)
Testing interactions between components, ensuring they work together properly.
- Database connection tests
- API endpoint tests
- Component interaction tests

### 3. End-to-End Tests (`e2e/`)
Testing complete workflows as a user would experience them.
- Database workflow tests
- Complete business process tests

## Running Tests

You can use pytest or unittest to run the tests:

```powershell
# Run all tests with pytest
pytest

# Run all tests with unittest
python -m unittest discover

# Run specific test categories
pytest tests/unit
pytest tests/integration
pytest tests/e2e

# Run a specific test file
pytest tests/unit/test_database_manager.py

# Run a specific category
python -m tests.run_tests --unit
python -m tests.run_tests --integration
python -m tests.run_tests --database
python -m tests.run_tests --api
python -m tests.run_tests --e2e

# Generate coverage report
python -m tests.run_tests --all --coverage
```

Or use pytest directly:

```bash
# Run all tests
pytest

# Run tests in a specific directory
pytest tests/unit
pytest tests/integration
pytest tests/e2e

# Run a specific test file
pytest tests/unit/test_upi_transactions.py
```

## Prerequisites

- MySQL database server running with proper schema
- Environment variables set or config files present
- For API tests, the API server must be running (`python run_api.py`)

## Fixtures and Helpers

Common test fixtures and helpers are defined in `conftest.py`.
