# Unit Tests

This directory contains unit tests for the Core Banking System.

Unit tests focus on testing individual components in isolation:
- Each test focuses on a specific function or class
- Dependencies are mocked or stubbed
- Tests are small and fast to run

## Test Categories

### Database Tests
- `test_database_manager.py`: Tests for database manager functionality (mocked, no actual DB connection)
- `test_account_model.py`: Tests for account model functionality
- `test_customer_model.py`: Tests for customer model functionality  
- `test_transaction_model.py`: Tests for transaction model functionality
- `test_upi_transactions.py`: Tests for UPI transactions functionality

## Running Unit Tests

```bash
# Run all unit tests
python -m unittest discover tests/unit

# Run a specific test file
python -m unittest tests/unit/test_file.py
```
