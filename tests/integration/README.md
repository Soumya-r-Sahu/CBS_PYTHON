# Integration Tests

This directory contains integration tests for the Core Banking System.

Integration tests focus on testing how different components work together:
- Tests interactions between components
- May use actual database connections
- Tests functionality across module boundaries

## Test Categories

### Database Integration Tests
- `test_database_connection.py`: Tests for database connections and operations
- `test_account_transactions.py`: Tests the interaction between accounts and transactions

### API Integration Tests
- `test_upi_api.py`: Tests for the UPI API endpoints

## Running Integration Tests

```bash
# Run all integration tests
python -m unittest discover tests/integration

# Run a specific test file
python -m unittest tests/integration/test_file.py
```
